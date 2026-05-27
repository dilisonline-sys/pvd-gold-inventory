"""
Reports views for the PVD Gold Inventory / Goldsmith Manufacturing system.

All views require manager-or-above access.  Each view queries the database
using Django ORM and passes a context dict to the corresponding template.
No placeholder data — all numbers come from real model queries.
"""

from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db.models import (
    Avg,
    Case,
    Count,
    DecimalField,
    DurationField,
    ExpressionWrapper,
    F,
    Q,
    Sum,
    When,
)
from django.db.models.functions import TruncDate, TruncMonth
from django.shortcuts import render
from django.utils import timezone

from accounts.decorators import manager_or_above
from inventory.models import (
    CurrentStock,
    MaterialCategory,
    RawMaterial,
    StockEntry,
    StockTransaction,
    Supplier,
    TRANSACTION_IN,
    TRANSACTION_OUT,
    TRANSACTION_WASTE,
)
from manufacturing.models import (
    MaterialIssuance,
    ProcessRecord,
    ProcessStage,
    ProductionJob,
    QualityCheck,
    RECORD_STATUS_COMPLETED,
    STATUS_COMPLETED as MFG_STATUS_COMPLETED,
    STATUS_IN_PROGRESS,
)
from orders.models import (
    Customer,
    JobOrder,
    ORDER_STATUS_CHOICES,
    STATUS_DELIVERED,
    STATUS_CANCELLED,
    METAL_TYPE_CHOICES,
)

User = get_user_model()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_date_range(request):
    """Return (date_from, date_to) from GET params, defaulting to last 30 days."""
    today = timezone.now().date()
    default_from = today - timedelta(days=30)

    date_from_str = request.GET.get('date_from', '')
    date_to_str = request.GET.get('date_to', '')

    try:
        date_from = date.fromisoformat(date_from_str) if date_from_str else default_from
    except ValueError:
        date_from = default_from

    try:
        date_to = date.fromisoformat(date_to_str) if date_to_str else today
    except ValueError:
        date_to = today

    return date_from, date_to


# ---------------------------------------------------------------------------
# Production Report
# ---------------------------------------------------------------------------

@manager_or_above
def production_report(request):
    """
    Production statistics:
    - Jobs by status
    - Jobs by current manufacturing stage
    - Completion rate (completed vs total)
    - Average time from creation to completion
    - Date-range filter applied to created_at
    """
    date_from, date_to = _parse_date_range(request)

    jobs_qs = ProductionJob.objects.filter(
        created_at__date__gte=date_from,
        created_at__date__lte=date_to,
    )

    # --- Jobs by status ---
    jobs_by_status = (
        jobs_qs
        .values('status')
        .annotate(count=Count('id'))
        .order_by('status')
    )

    # --- Jobs by current stage ---
    jobs_by_stage = (
        jobs_qs
        .values('current_stage__name', 'current_stage__order_number')
        .annotate(count=Count('id'))
        .order_by('current_stage__order_number')
    )

    # --- Overall counts ---
    total_jobs = jobs_qs.count()
    completed_jobs = jobs_qs.filter(status=MFG_STATUS_COMPLETED).count()
    in_progress_jobs = jobs_qs.filter(status=STATUS_IN_PROGRESS).count()
    completion_rate = (
        round(completed_jobs / total_jobs * 100, 1) if total_jobs else 0
    )

    # --- Process records: stage completion summary ---
    records_qs = ProcessRecord.objects.filter(
        production_job__in=jobs_qs
    )
    stage_summary = (
        records_qs
        .values('stage__name', 'stage__order_number')
        .annotate(
            total=Count('id'),
            completed=Count(Case(When(status=RECORD_STATUS_COMPLETED, then=1))),
        )
        .order_by('stage__order_number')
    )
    for row in stage_summary:
        row['completion_pct'] = (
            round(row['completed'] / row['total'] * 100, 1) if row['total'] else 0
        )

    # --- QC pass/fail summary ---
    qc_summary = (
        QualityCheck.objects
        .filter(process_record__production_job__in=jobs_qs)
        .values('result')
        .annotate(count=Count('id'))
        .order_by('result')
    )

    context = {
        'date_from': date_from,
        'date_to': date_to,
        'total_jobs': total_jobs,
        'completed_jobs': completed_jobs,
        'in_progress_jobs': in_progress_jobs,
        'completion_rate': completion_rate,
        'jobs_by_status': list(jobs_by_status),
        'jobs_by_stage': list(jobs_by_stage),
        'stage_summary': list(stage_summary),
        'qc_summary': list(qc_summary),
    }
    return render(request, 'reports/production_report.html', context)


# ---------------------------------------------------------------------------
# Inventory Report
# ---------------------------------------------------------------------------

@manager_or_above
def inventory_report(request):
    """
    Inventory statistics:
    - Current stock levels for all materials
    - Low-stock materials (below minimum)
    - Stock consumed (OUT transactions) in date range
    - Supplier summary: total value received per supplier
    """
    date_from, date_to = _parse_date_range(request)

    # --- Current stock ---
    all_materials = RawMaterial.objects.filter(is_active=True).select_related(
        'category', 'current_stock'
    )

    stock_levels = []
    low_stock_items = []
    for mat in all_materials:
        qty = mat.get_current_stock()
        stock_levels.append({
            'material': mat,
            'quantity': qty,
            'unit': mat.unit_of_measure,
            'minimum': mat.minimum_stock_level,
            'is_low': mat.is_low_stock,
        })
        if mat.is_low_stock:
            low_stock_items.append({
                'material': mat,
                'quantity': qty,
                'minimum': mat.minimum_stock_level,
                'shortage': mat.minimum_stock_level - qty,
            })

    # --- Consumption in date range (OUT transactions) ---
    consumption_qs = (
        StockTransaction.objects
        .filter(
            transaction_type=TRANSACTION_OUT,
            created_at__date__gte=date_from,
            created_at__date__lte=date_to,
        )
        .values('material__name', 'material__unit_of_measure', 'material__category__name')
        .annotate(total_consumed=Sum('quantity'))
        .order_by('-total_consumed')
    )

    # --- Waste in date range ---
    waste_qs = (
        StockTransaction.objects
        .filter(
            transaction_type=TRANSACTION_WASTE,
            created_at__date__gte=date_from,
            created_at__date__lte=date_to,
        )
        .values('material__name', 'material__unit_of_measure')
        .annotate(total_waste=Sum('quantity'))
        .order_by('-total_waste')
    )

    # --- Stock received in date range (IN transactions) ---
    received_qs = (
        StockTransaction.objects
        .filter(
            transaction_type=TRANSACTION_IN,
            created_at__date__gte=date_from,
            created_at__date__lte=date_to,
        )
        .aggregate(
            total_transactions=Count('id'),
            total_qty=Sum('quantity'),
        )
    )

    # --- Supplier summary: stock entries in date range ---
    supplier_summary = (
        StockEntry.objects
        .filter(
            entry_date__gte=date_from,
            entry_date__lte=date_to,
            supplier__isnull=False,
        )
        .values('supplier__name')
        .annotate(
            total_entries=Count('id'),
            total_value=Sum('total_cost'),
        )
        .order_by('-total_value')
    )

    # --- Category breakdown of current stock count ---
    category_breakdown = (
        RawMaterial.objects
        .filter(is_active=True)
        .values('category__name')
        .annotate(material_count=Count('id'))
        .order_by('category__name')
    )

    total_materials = all_materials.count()
    low_stock_count = len(low_stock_items)

    context = {
        'date_from': date_from,
        'date_to': date_to,
        'stock_levels': stock_levels,
        'low_stock_items': low_stock_items,
        'total_materials': total_materials,
        'low_stock_count': low_stock_count,
        'consumption': list(consumption_qs),
        'waste': list(waste_qs),
        'received': received_qs,
        'supplier_summary': list(supplier_summary),
        'category_breakdown': list(category_breakdown),
    }
    return render(request, 'reports/inventory_report.html', context)


# ---------------------------------------------------------------------------
# Order Report
# ---------------------------------------------------------------------------

@manager_or_above
def order_report(request):
    """
    Order statistics:
    - Orders by status
    - Orders by metal type
    - Revenue summary (estimated vs actual, advance payments, balance due)
    - Top customers by order count / revenue
    - Monthly order volume trend
    """
    date_from, date_to = _parse_date_range(request)

    orders_qs = JobOrder.objects.filter(
        order_date__gte=date_from,
        order_date__lte=date_to,
    )

    # --- Orders by status ---
    orders_by_status = (
        orders_qs
        .values('status')
        .annotate(count=Count('id'))
        .order_by('status')
    )
    status_map = dict(ORDER_STATUS_CHOICES)
    for row in orders_by_status:
        row['status_display'] = status_map.get(row['status'], row['status'])

    # --- Orders by metal type ---
    orders_by_metal = (
        orders_qs
        .values('metal_type')
        .annotate(count=Count('id'))
        .order_by('-count')
    )

    # --- Orders by metal purity ---
    orders_by_purity = (
        orders_qs
        .values('metal_purity')
        .annotate(count=Count('id'))
        .order_by('-count')
    )

    # --- Revenue summary ---
    financials = orders_qs.aggregate(
        total_estimated=Sum('estimated_cost'),
        total_actual=Sum('actual_cost'),
        total_advance=Sum('advance_payment'),
        order_count=Count('id'),
    )
    total_estimated = financials['total_estimated'] or Decimal('0')
    total_actual = financials['total_actual'] or Decimal('0')
    total_advance = financials['total_advance'] or Decimal('0')
    # balance due = sum(actual_cost or estimated_cost) - sum(advance)
    effective_cost = total_actual if total_actual else total_estimated
    total_balance_due = effective_cost - total_advance

    # --- Top customers by order count ---
    top_customers_by_count = (
        orders_qs
        .values('customer__name', 'customer__id')
        .annotate(order_count=Count('id'))
        .order_by('-order_count')[:10]
    )

    # --- Top customers by estimated revenue ---
    top_customers_by_revenue = (
        orders_qs
        .values('customer__name', 'customer__id')
        .annotate(total_revenue=Sum('estimated_cost'))
        .order_by('-total_revenue')[:10]
    )

    # --- Monthly trend (orders per month) ---
    monthly_trend = (
        orders_qs
        .annotate(month=TruncMonth('order_date'))
        .values('month')
        .annotate(count=Count('id'), revenue=Sum('estimated_cost'))
        .order_by('month')
    )

    # --- Delivery performance ---
    delivered_qs = orders_qs.filter(status=STATUS_DELIVERED)
    on_time = delivered_qs.filter(delivery_date__lte=F('required_date')).count()
    late = delivered_qs.filter(delivery_date__gt=F('required_date')).count()
    total_delivered = delivered_qs.count()

    context = {
        'date_from': date_from,
        'date_to': date_to,
        'order_count': financials['order_count'],
        'orders_by_status': list(orders_by_status),
        'orders_by_metal': list(orders_by_metal),
        'orders_by_purity': list(orders_by_purity),
        'total_estimated': total_estimated,
        'total_actual': total_actual,
        'total_advance': total_advance,
        'total_balance_due': total_balance_due,
        'top_customers_by_count': list(top_customers_by_count),
        'top_customers_by_revenue': list(top_customers_by_revenue),
        'monthly_trend': list(monthly_trend),
        'total_delivered': total_delivered,
        'on_time_deliveries': on_time,
        'late_deliveries': late,
        'on_time_pct': round(on_time / total_delivered * 100, 1) if total_delivered else 0,
    }
    return render(request, 'reports/order_report.html', context)


# ---------------------------------------------------------------------------
# Gold Consumption Report
# ---------------------------------------------------------------------------

@manager_or_above
def gold_consumption_report(request):
    """
    Gold weight tracking:
    - Total gold received (stock entries for Gold category) in date range
    - Total gold issued to production (MaterialIssuance for gold materials)
    - Weight in vs weight out per production job (via ProcessRecord)
    - Waste/loss per job and in total
    """
    date_from, date_to = _parse_date_range(request)

    # --- Gold stock received ---
    gold_received = (
        StockEntry.objects
        .filter(
            material__category__name=MaterialCategory.GOLD,
            entry_date__gte=date_from,
            entry_date__lte=date_to,
        )
        .aggregate(
            total_qty=Sum('quantity'),
            total_cost=Sum('total_cost'),
            entry_count=Count('id'),
        )
    )

    # --- Gold issued to production ---
    gold_issued = (
        MaterialIssuance.objects
        .filter(
            material__category__name=MaterialCategory.GOLD,
            issued_at__date__gte=date_from,
            issued_at__date__lte=date_to,
        )
        .aggregate(
            total_issued=Sum('quantity_issued'),
            issuance_count=Count('id'),
        )
    )

    # --- Per-job weight tracking via ProcessRecords ---
    job_weight_summary = (
        ProcessRecord.objects
        .filter(
            production_job__created_at__date__gte=date_from,
            production_job__created_at__date__lte=date_to,
            weight_in__isnull=False,
        )
        .values(
            'production_job__job_number',
            'production_job__title',
            'production_job__id',
        )
        .annotate(
            total_weight_in=Sum('weight_in'),
            total_weight_out=Sum('weight_out'),
            total_waste=Sum('waste_weight'),
        )
        .order_by('production_job__job_number')
    )

    # Compute loss per job
    job_weight_rows = []
    total_weight_in = Decimal('0')
    total_weight_out = Decimal('0')
    total_waste_weight = Decimal('0')
    for row in job_weight_summary:
        wi = row['total_weight_in'] or Decimal('0')
        wo = row['total_weight_out'] or Decimal('0')
        ww = row['total_waste'] or Decimal('0')
        loss = wi - wo
        loss_pct = round(float(loss) / float(wi) * 100, 2) if wi else 0
        job_weight_rows.append({
            'job_number': row['production_job__job_number'],
            'job_title': row['production_job__title'],
            'job_id': row['production_job__id'],
            'weight_in': wi,
            'weight_out': wo,
            'waste': ww,
            'loss': loss,
            'loss_pct': loss_pct,
        })
        total_weight_in += wi
        total_weight_out += wo
        total_waste_weight += ww

    total_loss = total_weight_in - total_weight_out
    overall_loss_pct = (
        round(float(total_loss) / float(total_weight_in) * 100, 2)
        if total_weight_in else 0
    )

    # --- Stage-level weight loss breakdown ---
    stage_weight = (
        ProcessRecord.objects
        .filter(
            production_job__created_at__date__gte=date_from,
            production_job__created_at__date__lte=date_to,
            weight_in__isnull=False,
            weight_out__isnull=False,
        )
        .values('stage__name', 'stage__order_number')
        .annotate(
            total_in=Sum('weight_in'),
            total_out=Sum('weight_out'),
            total_waste=Sum('waste_weight'),
        )
        .order_by('stage__order_number')
    )
    stage_weight_rows = []
    for row in stage_weight:
        wi = row['total_in'] or Decimal('0')
        wo = row['total_out'] or Decimal('0')
        loss = wi - wo
        loss_pct = round(float(loss) / float(wi) * 100, 2) if wi else 0
        stage_weight_rows.append({
            'stage': row['stage__name'],
            'weight_in': wi,
            'weight_out': wo,
            'waste': row['total_waste'] or Decimal('0'),
            'loss': loss,
            'loss_pct': loss_pct,
        })

    context = {
        'date_from': date_from,
        'date_to': date_to,
        'gold_received': gold_received,
        'gold_issued': gold_issued,
        'job_weight_rows': job_weight_rows,
        'total_weight_in': total_weight_in,
        'total_weight_out': total_weight_out,
        'total_waste_weight': total_waste_weight,
        'total_loss': total_loss,
        'overall_loss_pct': overall_loss_pct,
        'stage_weight_rows': stage_weight_rows,
    }
    return render(request, 'reports/gold_consumption.html', context)


# ---------------------------------------------------------------------------
# Worker Productivity Report
# ---------------------------------------------------------------------------

@manager_or_above
def worker_productivity(request):
    """
    Worker productivity statistics:
    - Number of process records completed per worker in date range
    - Average time spent per stage per worker (completed_at - started_at)
    - QC pass rate per worker
    - Material issuances handled per worker
    """
    date_from, date_to = _parse_date_range(request)

    # --- Process records completed per worker ---
    worker_records = (
        ProcessRecord.objects
        .filter(
            status=RECORD_STATUS_COMPLETED,
            completed_at__date__gte=date_from,
            completed_at__date__lte=date_to,
            assigned_to__isnull=False,
        )
        .values(
            'assigned_to__id',
            'assigned_to__username',
            'assigned_to__first_name',
            'assigned_to__last_name',
        )
        .annotate(
            records_completed=Count('id'),
        )
        .order_by('-records_completed')
    )

    # --- Average duration per worker (where both started_at and completed_at set) ---
    worker_duration = (
        ProcessRecord.objects
        .filter(
            status=RECORD_STATUS_COMPLETED,
            completed_at__date__gte=date_from,
            completed_at__date__lte=date_to,
            assigned_to__isnull=False,
            started_at__isnull=False,
            completed_at__isnull=False,
        )
        .values(
            'assigned_to__id',
            'assigned_to__username',
        )
        .annotate(
            avg_duration=Avg(
                ExpressionWrapper(
                    F('completed_at') - F('started_at'),
                    output_field=DurationField(),
                )
            )
        )
    )
    duration_map = {
        row['assigned_to__id']: row['avg_duration']
        for row in worker_duration
    }

    # --- QC checks per worker ---
    worker_qc = (
        QualityCheck.objects
        .filter(
            checked_at__date__gte=date_from,
            checked_at__date__lte=date_to,
        )
        .values('checked_by__id', 'checked_by__username')
        .annotate(
            total_checks=Count('id'),
            passed=Count(Case(When(result='PASS', then=1))),
        )
    )
    qc_map = {
        row['checked_by__id']: {
            'total_checks': row['total_checks'],
            'passed': row['passed'],
        }
        for row in worker_qc
    }

    # --- Material issuances per worker ---
    issuance_per_worker = (
        MaterialIssuance.objects
        .filter(
            issued_at__date__gte=date_from,
            issued_at__date__lte=date_to,
        )
        .values('issued_by__id', 'issued_by__username')
        .annotate(issuances=Count('id'))
    )
    issuance_map = {
        row['issued_by__id']: row['issuances']
        for row in issuance_per_worker
    }

    # --- Stage breakdown: jobs processed per stage ---
    stage_productivity = (
        ProcessRecord.objects
        .filter(
            status=RECORD_STATUS_COMPLETED,
            completed_at__date__gte=date_from,
            completed_at__date__lte=date_to,
        )
        .values('stage__name', 'stage__order_number')
        .annotate(completed_count=Count('id'))
        .order_by('stage__order_number')
    )

    # Build merged worker productivity rows
    productivity_rows = []
    for row in worker_records:
        uid = row['assigned_to__id']
        first = row['assigned_to__first_name'] or ''
        last = row['assigned_to__last_name'] or ''
        display_name = f'{first} {last}'.strip() or row['assigned_to__username']

        qc_data = qc_map.get(uid, {'total_checks': 0, 'passed': 0})
        qc_pass_rate = (
            round(qc_data['passed'] / qc_data['total_checks'] * 100, 1)
            if qc_data['total_checks'] else None
        )

        avg_dur = duration_map.get(uid)
        avg_hours = round(avg_dur.total_seconds() / 3600, 2) if avg_dur else None

        productivity_rows.append({
            'user_id': uid,
            'username': row['assigned_to__username'],
            'display_name': display_name,
            'records_completed': row['records_completed'],
            'avg_duration_hours': avg_hours,
            'total_qc_checks': qc_data['total_checks'],
            'qc_pass_rate': qc_pass_rate,
            'issuances_handled': issuance_map.get(uid, 0),
        })

    context = {
        'date_from': date_from,
        'date_to': date_to,
        'productivity_rows': productivity_rows,
        'stage_productivity': list(stage_productivity),
        'total_workers': len(productivity_rows),
        'total_records_completed': sum(r['records_completed'] for r in productivity_rows),
    }
    return render(request, 'reports/worker_productivity.html', context)
