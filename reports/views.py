"""
Reports views — all require manager-or-above access.
All queries use real model data; no placeholder values.
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
from django.db.models.functions import TruncMonth
from django.shortcuts import render
from django.utils import timezone

from accounts.decorators import manager_or_above
from inventory.models import (
    CurrentStock,
    MaterialCategory,
    RawMaterial,
    StockEntry,
    StockTransaction,
    TRANSACTION_IN,
    TRANSACTION_OUT,
    TRANSACTION_WASTE,
)
from manufacturing.models import (
    FinalProduct,
    MaterialIssuance,
    MaterialRequirement,
    ProcessRecord,
    ProcessStage,
    ProductionJob,
    QualityCheck,
    RECORD_STATUS_COMPLETED,
    STATUS_CANCELLED,
    STATUS_COMPLETED as MFG_STATUS_COMPLETED,
    STATUS_IN_PROGRESS,
)
from orders.models import (
    Customer,
    JobOrder,
    ORDER_STATUS_CHOICES,
    METAL_PURITY_CHOICES,
    STATUS_DELIVERED,
    STATUS_CANCELLED as ORDER_CANCELLED,
)

User = get_user_model()

# Purity display lookup from orders choices
_PURITY_DISPLAY = {val: label for val, label in METAL_PURITY_CHOICES}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_date_range(request):
    """Return (date_from, date_to) from GET params, defaulting to last 30 days."""
    today = timezone.now().date()
    default_from = today - timedelta(days=30)

    try:
        date_from = date.fromisoformat(request.GET.get('date_from', ''))
    except (ValueError, TypeError):
        date_from = default_from

    try:
        date_to = date.fromisoformat(request.GET.get('date_to', ''))
    except (ValueError, TypeError):
        date_to = today

    return date_from, date_to


# ---------------------------------------------------------------------------
# Production Report
# ---------------------------------------------------------------------------

@manager_or_above
def production_report(request):
    date_from, date_to = _parse_date_range(request)

    jobs_qs = ProductionJob.objects.filter(
        created_at__date__gte=date_from,
        created_at__date__lte=date_to,
    )

    total_jobs = jobs_qs.count()
    completed_jobs = jobs_qs.filter(status=MFG_STATUS_COMPLETED).count()
    in_progress_jobs = jobs_qs.filter(status=STATUS_IN_PROGRESS).count()
    cancelled_jobs = jobs_qs.filter(status=STATUS_CANCELLED).count()
    completion_rate = round(completed_jobs / total_jobs * 100, 1) if total_jobs else 0

    # Stage breakdown: how many jobs are currently at each stage (by status)
    stage_raw = (
        jobs_qs
        .values('current_stage__name', 'current_stage__order_number', 'status')
        .annotate(count=Count('id'))
        .order_by('current_stage__order_number')
    )
    stage_dict = {}
    stage_order = {}
    for row in stage_raw:
        name = row['current_stage__name'] or 'Unknown'
        stage_order[name] = row['current_stage__order_number'] or 99
        if name not in stage_dict:
            stage_dict[name] = {'stage': name, 'active': 0, 'completed': 0, 'other': 0}
        if row['status'] == STATUS_IN_PROGRESS:
            stage_dict[name]['active'] += row['count']
        elif row['status'] == MFG_STATUS_COMPLETED:
            stage_dict[name]['completed'] += row['count']
        else:
            stage_dict[name]['other'] += row['count']
    stage_breakdown = sorted(stage_dict.values(), key=lambda r: stage_order.get(r['stage'], 99))

    # QC summary with percentage
    qc_raw = (
        QualityCheck.objects
        .filter(process_record__production_job__in=jobs_qs)
        .values('result')
        .annotate(count=Count('id'))
        .order_by('result')
    )
    qc_list = list(qc_raw)
    total_qc = sum(r['count'] for r in qc_list)
    qc_summary = [
        {**r, 'pct': round(r['count'] / total_qc * 100, 1) if total_qc else 0}
        for r in qc_list
    ]

    # Material shortfalls for active jobs
    active_reqs = (
        MaterialRequirement.objects
        .filter(production_job__in=jobs_qs, production_job__status=STATUS_IN_PROGRESS)
        .select_related('material', 'material__current_stock', 'production_job')
    )
    shortfall_count = sum(1 for r in active_reqs if not r.is_available)

    # Catalog entries created in this period
    catalog_count = FinalProduct.objects.filter(
        created_at__date__gte=date_from,
        created_at__date__lte=date_to,
    ).count()

    context = {
        'date_from': date_from,
        'date_to': date_to,
        'total_jobs': total_jobs,
        'completed_jobs': completed_jobs,
        'in_progress_jobs': in_progress_jobs,
        'cancelled_jobs': cancelled_jobs,
        'completion_rate': completion_rate,
        'stage_breakdown': stage_breakdown,
        'qc_summary': qc_summary,
        'shortfall_count': shortfall_count,
        'catalog_count': catalog_count,
    }
    return render(request, 'reports/production_report.html', context)


# ---------------------------------------------------------------------------
# Inventory Report
# ---------------------------------------------------------------------------

@manager_or_above
def inventory_report(request):
    date_from, date_to = _parse_date_range(request)

    all_materials = (
        RawMaterial.objects
        .filter(is_active=True)
        .select_related('category', 'current_stock')
        .order_by('category__name', 'name')
    )

    materials_data = []
    for mat in all_materials:
        qty = mat.get_current_stock()
        materials_data.append({
            'name': mat.name,
            'category': mat.category.name,
            'metal_type': mat.metal_type,
            'metal_purity': _PURITY_DISPLAY.get(mat.metal_purity, mat.metal_purity),
            'unit': mat.unit_of_measure,
            'on_hand': qty,
            'min_level': mat.minimum_stock_level,
            'is_low': mat.is_low_stock,
            'pk': mat.pk,
        })

    total_materials = len(materials_data)
    low_stock_count = sum(1 for m in materials_data if m['is_low'])

    # Totals for the date range
    total_received = (
        StockTransaction.objects
        .filter(transaction_type=TRANSACTION_IN, created_at__date__gte=date_from, created_at__date__lte=date_to)
        .aggregate(total=Sum('quantity'))['total'] or Decimal('0')
    )
    total_consumed = (
        StockTransaction.objects
        .filter(transaction_type=TRANSACTION_OUT, created_at__date__gte=date_from, created_at__date__lte=date_to)
        .aggregate(total=Sum('quantity'))['total'] or Decimal('0')
    )
    total_waste = (
        StockTransaction.objects
        .filter(transaction_type=TRANSACTION_WASTE, created_at__date__gte=date_from, created_at__date__lte=date_to)
        .aggregate(total=Sum('quantity'))['total'] or Decimal('0')
    )

    # Consumption breakdown by material
    consumption = (
        StockTransaction.objects
        .filter(transaction_type=TRANSACTION_OUT, created_at__date__gte=date_from, created_at__date__lte=date_to)
        .values('material__name', 'material__unit_of_measure', 'material__category__name')
        .annotate(total_consumed=Sum('quantity'))
        .order_by('-total_consumed')
    )

    # Supplier summary
    supplier_summary = (
        StockEntry.objects
        .filter(entry_date__gte=date_from, entry_date__lte=date_to, supplier__isnull=False)
        .values('supplier__name')
        .annotate(total_entries=Count('id'), total_value=Sum('total_cost'))
        .order_by('-total_value')
    )

    # Category summary
    category_raw = (
        RawMaterial.objects
        .filter(is_active=True)
        .values('category__name')
        .annotate(material_count=Count('id'))
        .order_by('category__name')
    )
    category_summary = [
        {'category': r['category__name'], 'count': r['material_count']}
        for r in category_raw
    ]

    # Material requirement shortfalls for active jobs
    all_reqs = (
        MaterialRequirement.objects
        .filter(production_job__status__in=('PENDING', 'IN_PROGRESS', 'ON_HOLD'))
        .select_related(
            'material', 'material__current_stock',
            'production_job', 'production_job__current_stage',
        )
        .order_by('production_job__job_number', 'material__name')
    )
    shortfall_items = [r for r in all_reqs if not r.is_available]

    context = {
        'date_from': date_from,
        'date_to': date_to,
        'materials_data': materials_data,
        'total_materials': total_materials,
        'low_stock_count': low_stock_count,
        'total_received': total_received,
        'total_consumed': total_consumed,
        'total_waste': total_waste,
        'consumption': list(consumption),
        'supplier_summary': list(supplier_summary),
        'category_summary': category_summary,
        'shortfall_items': shortfall_items,
        'shortfall_count': len(shortfall_items),
    }
    return render(request, 'reports/inventory_report.html', context)


# ---------------------------------------------------------------------------
# Order Report
# ---------------------------------------------------------------------------

@manager_or_above
def order_report(request):
    date_from, date_to = _parse_date_range(request)

    orders_qs = JobOrder.objects.filter(
        order_date__gte=date_from,
        order_date__lte=date_to,
    )

    total_orders = orders_qs.count()
    delivered_orders = orders_qs.filter(status=STATUS_DELIVERED).count()

    # Financial summary (handle nullable estimated_cost)
    financials = orders_qs.aggregate(
        total_estimated=Sum('estimated_cost'),
        total_actual=Sum('actual_cost'),
        total_advance=Sum('advance_payment'),
    )
    total_estimated = financials['total_estimated'] or Decimal('0')
    total_actual = financials['total_actual'] or Decimal('0')
    total_advance = financials['total_advance'] or Decimal('0')
    total_revenue = total_actual if total_actual else total_estimated
    total_balance_due = total_revenue - total_advance

    # Status breakdown with revenue
    status_raw = (
        orders_qs
        .values('status')
        .annotate(count=Count('id'), revenue=Sum('estimated_cost'))
        .order_by('status')
    )
    status_map = dict(ORDER_STATUS_CHOICES)
    status_counts = [
        {
            'status': status_map.get(r['status'], r['status']),
            'count': r['count'],
            'revenue': r['revenue'] or Decimal('0'),
        }
        for r in status_raw
    ]

    # Top customers (by order count, with revenue)
    top_customers = list(
        orders_qs
        .values('customer__name', 'customer__id')
        .annotate(total_orders=Count('id'), total_revenue=Sum('estimated_cost'))
        .order_by('-total_orders')[:10]
    )

    # Orders by metal type + purity combined
    metal_type_counts = list(
        orders_qs
        .values('metal_type', 'metal_purity')
        .annotate(count=Count('id'))
        .order_by('-count')
    )
    # Add display label for purity
    for row in metal_type_counts:
        row['metal_purity_display'] = _PURITY_DISPLAY.get(row['metal_purity'], row['metal_purity'])

    # Monthly trend
    monthly_trend = list(
        orders_qs
        .annotate(month=TruncMonth('order_date'))
        .values('month')
        .annotate(count=Count('id'), revenue=Sum('estimated_cost'))
        .order_by('month')
    )

    # Delivery performance
    delivered_qs = orders_qs.filter(status=STATUS_DELIVERED)
    on_time = delivered_qs.filter(delivery_date__lte=F('required_date')).count()
    late = delivered_qs.filter(delivery_date__gt=F('required_date')).count()
    total_delivered = delivered_qs.count()
    on_time_rate = round(on_time / total_delivered * 100, 1) if total_delivered else 0

    context = {
        'date_from': date_from,
        'date_to': date_to,
        'total_orders': total_orders,
        'delivered_orders': delivered_orders,
        'total_revenue': total_revenue,
        'total_estimated': total_estimated,
        'total_actual': total_actual,
        'total_advance': total_advance,
        'total_balance_due': total_balance_due,
        'on_time_rate': on_time_rate,
        'on_time_deliveries': on_time,
        'late_deliveries': late,
        'total_delivered': total_delivered,
        'status_counts': status_counts,
        'top_customers': top_customers,
        'metal_type_counts': metal_type_counts,
        'monthly_trend': monthly_trend,
    }
    return render(request, 'reports/order_report.html', context)


# ---------------------------------------------------------------------------
# Gold Consumption Report
# ---------------------------------------------------------------------------

@manager_or_above
def gold_consumption_report(request):
    date_from, date_to = _parse_date_range(request)

    # Gold received in date range
    gold_received = (
        StockEntry.objects
        .filter(
            material__category__name=MaterialCategory.GOLD,
            entry_date__gte=date_from,
            entry_date__lte=date_to,
        )
        .aggregate(total_qty=Sum('quantity'), total_cost=Sum('total_cost'), entry_count=Count('id'))
    )

    # Gold issued to production
    gold_issued = (
        MaterialIssuance.objects
        .filter(
            material__category__name=MaterialCategory.GOLD,
            issued_at__date__gte=date_from,
            issued_at__date__lte=date_to,
        )
        .aggregate(total_issued=Sum('quantity_issued'), issuance_count=Count('id'))
    )

    # Also include gold purity-tagged materials beyond category
    gold_purity_issued = (
        MaterialIssuance.objects
        .filter(
            Q(material__category__name=MaterialCategory.GOLD) | Q(material__metal_type='Gold'),
            issued_at__date__gte=date_from,
            issued_at__date__lte=date_to,
        )
        .values('material__name', 'material__metal_purity', 'material__unit_of_measure')
        .annotate(total=Sum('quantity_issued'))
        .order_by('-total')
    )

    # Per-job weight tracking via ProcessRecords
    job_weight_summary = (
        ProcessRecord.objects
        .filter(
            production_job__created_at__date__gte=date_from,
            production_job__created_at__date__lte=date_to,
            weight_in__isnull=False,
        )
        .values('production_job__job_number', 'production_job__title', 'production_job__id')
        .annotate(
            total_weight_in=Sum('weight_in'),
            total_weight_out=Sum('weight_out'),
            total_waste=Sum('waste_weight'),
        )
        .order_by('production_job__job_number')
    )

    total_weight_in = Decimal('0')
    total_weight_out = Decimal('0')
    total_waste_weight = Decimal('0')
    job_data = []
    for row in job_weight_summary:
        wi = row['total_weight_in'] or Decimal('0')
        wo = row['total_weight_out'] or Decimal('0')
        ww = row['total_waste'] or Decimal('0')
        loss = wi - wo
        loss_pct = round(float(loss) / float(wi) * 100, 2) if wi else 0
        job_data.append({
            'job_pk': row['production_job__id'],
            'job_number': row['production_job__job_number'],
            'title': row['production_job__title'] or '',
            'weight_in': wi,
            'weight_out': wo,
            'waste': ww,
            'loss_pct': loss_pct,
        })
        total_weight_in += wi
        total_weight_out += wo
        total_waste_weight += ww

    total_loss = total_weight_in - total_weight_out
    overall_loss_pct = (
        round(float(total_loss) / float(total_weight_in) * 100, 2) if total_weight_in else 0
    )

    # Stage-level weight loss
    stage_weight_raw = (
        ProcessRecord.objects
        .filter(
            production_job__created_at__date__gte=date_from,
            production_job__created_at__date__lte=date_to,
            weight_in__isnull=False,
            weight_out__isnull=False,
        )
        .values('stage__name', 'stage__order_number')
        .annotate(total_in=Sum('weight_in'), total_out=Sum('weight_out'), total_waste=Sum('waste_weight'))
        .order_by('stage__order_number')
    )
    stage_weight_rows = []
    for row in stage_weight_raw:
        wi = row['total_in'] or Decimal('0')
        wo = row['total_out'] or Decimal('0')
        loss = wi - wo
        stage_weight_rows.append({
            'stage': row['stage__name'],
            'weight_in': wi,
            'weight_out': wo,
            'waste': row['total_waste'] or Decimal('0'),
            'loss': loss,
            'loss_pct': round(float(loss) / float(wi) * 100, 2) if wi else 0,
        })

    totals = {
        'total_received': gold_received['total_qty'] or Decimal('0'),
        'total_issued': gold_issued['total_issued'] or Decimal('0'),
        'total_waste': total_waste_weight,
        'loss_pct': overall_loss_pct,
    }

    context = {
        'date_from': date_from,
        'date_to': date_to,
        'totals': totals,
        'gold_received': gold_received,
        'gold_issued': gold_issued,
        'gold_purity_issued': list(gold_purity_issued),
        'job_data': job_data,
        'stage_weight_rows': stage_weight_rows,
        'total_weight_in': total_weight_in,
        'total_weight_out': total_weight_out,
        'total_loss': total_loss,
    }
    return render(request, 'reports/gold_consumption.html', context)


# ---------------------------------------------------------------------------
# Worker Productivity Report
# ---------------------------------------------------------------------------

@manager_or_above
def worker_productivity(request):
    date_from, date_to = _parse_date_range(request)

    # Completed records per worker
    worker_records = (
        ProcessRecord.objects
        .filter(
            status=RECORD_STATUS_COMPLETED,
            completed_at__date__gte=date_from,
            completed_at__date__lte=date_to,
            assigned_to__isnull=False,
        )
        .values('assigned_to__id', 'assigned_to__username', 'assigned_to__first_name', 'assigned_to__last_name', 'assigned_to__role')
        .annotate(records_completed=Count('id'))
        .order_by('-records_completed')
    )

    # Average duration per worker
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
        .values('assigned_to__id')
        .annotate(
            avg_duration=Avg(
                ExpressionWrapper(F('completed_at') - F('started_at'), output_field=DurationField())
            )
        )
    )
    duration_map = {r['assigned_to__id']: r['avg_duration'] for r in worker_duration}

    # QC checks per worker
    worker_qc = (
        QualityCheck.objects
        .filter(checked_at__date__gte=date_from, checked_at__date__lte=date_to)
        .values('checked_by__id', 'checked_by__username')
        .annotate(total_checks=Count('id'), passed=Count(Case(When(result='PASS', then=1))))
    )
    qc_map = {r['checked_by__id']: r for r in worker_qc}

    # Material issuances per worker
    issuance_map = {
        r['issued_by__id']: r['issuances']
        for r in (
            MaterialIssuance.objects
            .filter(issued_at__date__gte=date_from, issued_at__date__lte=date_to)
            .values('issued_by__id')
            .annotate(issuances=Count('id'))
        )
    }

    # Stage productivity (completed records per stage)
    stage_productivity = list(
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

    # Build worker_data rows
    worker_data = []
    for row in worker_records:
        uid = row['assigned_to__id']
        first = row['assigned_to__first_name'] or ''
        last = row['assigned_to__last_name'] or ''
        display_name = f'{first} {last}'.strip() or row['assigned_to__username']
        role = row.get('assigned_to__role', '')

        qc_data = qc_map.get(uid, {'total_checks': 0, 'passed': 0})
        total_checks = qc_data.get('total_checks', 0) or 0
        passed = qc_data.get('passed', 0) or 0
        qc_pass_rate = round(passed / total_checks * 100, 1) if total_checks else None

        avg_dur = duration_map.get(uid)
        avg_hours = round(avg_dur.total_seconds() / 3600, 2) if avg_dur else None

        worker_data.append({
            'worker_name': display_name,
            'username': row['assigned_to__username'],
            'department': role.replace('_', ' ').title() if role else '—',
            'stages_completed': row['records_completed'],
            'avg_hours': avg_hours,
            'qc_pass_rate': qc_pass_rate,
            'materials_handled': issuance_map.get(uid, 0),
        })

    context = {
        'date_from': date_from,
        'date_to': date_to,
        'worker_data': worker_data,
        'stage_productivity': stage_productivity,
        'total_workers': len(worker_data),
        'total_records_completed': sum(r['stages_completed'] for r in worker_data),
    }
    return render(request, 'reports/worker_productivity.html', context)
