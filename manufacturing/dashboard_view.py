from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import timezone

from inventory.models import RawMaterial, StockTransaction
from manufacturing.models import ProcessStage, ProductionJob, JOB_STATUS_CHOICES
from orders.models import JobOrder


@login_required
def main_dashboard(request):
    today = timezone.now().date()

    # Production stats
    all_jobs = ProductionJob.objects.select_related('current_stage', 'job_order').order_by('-created_at')
    total_jobs = all_jobs.count()
    active_jobs = all_jobs.filter(status='IN_PROGRESS').count()
    completed_today = all_jobs.filter(status='COMPLETED', actual_completion_date=today).count()
    pending_jobs = all_jobs.filter(status='PENDING').count()

    recent_jobs = all_jobs[:8]

    overdue_jobs = all_jobs.filter(
        target_completion_date__lt=today,
        status__in=['IN_PROGRESS', 'PENDING'],
    ).count()

    # Order stats
    recent_orders = JobOrder.objects.select_related('customer', 'item_type').order_by('-created_at')[:8]
    total_orders = JobOrder.objects.count()
    orders_ready = JobOrder.objects.filter(status='READY').count()

    # Inventory alerts
    low_stock_items = [m for m in RawMaterial.objects.filter(is_active=True) if m.is_low_stock]
    low_stock_count = len(low_stock_items)

    # Stage distribution
    stages = ProcessStage.objects.filter(is_active=True).order_by('order_number')
    stage_data = []
    for stage in stages:
        count = all_jobs.filter(current_stage=stage, status='IN_PROGRESS').count()
        stage_data.append({'stage': stage, 'count': count})

    # Status breakdown
    status_counts = {label: all_jobs.filter(status=value).count() for value, label in JOB_STATUS_CHOICES}

    context = {
        'total_jobs': total_jobs,
        'active_jobs': active_jobs,
        'completed_today': completed_today,
        'pending_jobs': pending_jobs,
        'overdue_jobs': overdue_jobs,
        'total_orders': total_orders,
        'orders_ready': orders_ready,
        'low_stock_count': low_stock_count,
        'low_stock_items': low_stock_items[:5],
        'recent_jobs': recent_jobs,
        'recent_orders': recent_orders,
        'stage_data': stage_data,
        'status_counts': status_counts,
    }
    return render(request, 'dashboard.html', context)
