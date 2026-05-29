import re

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from accounts.decorators import supervisor_or_above
from accounts.models import ROLE_ADMIN


def _check_metal_stock(order):
    """Return (in_stock: bool, warning_msg: str | None) for the order's metal type + purity."""
    from inventory.models import RawMaterial

    metal_kw = order.metal_type  # 'Gold', 'Silver', 'Platinum', 'Other'
    purity_raw = order.metal_purity  # '18K', '925Silver', '950Platinum', etc.

    # Derive a search keyword from purity
    if purity_raw in ('Other', ''):
        purity_kw = None
    elif purity_raw.endswith('Silver') or purity_raw.endswith('Platinum'):
        m = re.match(r'^(\d+)', purity_raw)
        purity_kw = m.group(1) if m else None  # '925', '950'
    else:
        purity_kw = purity_raw  # '18K', '22K', etc.

    qs = RawMaterial.objects.filter(is_active=True, name__icontains=metal_kw)
    if purity_kw:
        qs = qs.filter(name__icontains=purity_kw)
    qs = qs.select_related('current_stock')

    matching = list(qs)
    if not matching:
        label = f'{order.get_metal_type_display()} {order.metal_purity}'
        return False, (
            f'No raw material found in inventory for {label}. '
            'Please add stock before starting production.'
        )

    in_stock = [m for m in matching if m.get_current_stock() > 0]
    if not in_stock:
        names = ', '.join(m.name for m in matching)
        return False, (
            f'Stock alert: {names} is at zero. '
            'Replenish inventory before starting production for this order.'
        )

    return True, None
from .forms import (
    CustomerForm,
    JobOrderForm,
    OrderDeliveryForm,
    OrderNoteForm,
    OrderStatusUpdateForm,
)
from .models import (
    Customer,
    JobOrder,
    OrderNote,
    STATUS_DELIVERED,
    STATUS_CANCELLED,
)


# ---------------------------------------------------------------------------
# Order List
# ---------------------------------------------------------------------------

@login_required
def order_list(request):
    """List all job orders with optional filters."""
    qs = JobOrder.objects.select_related('customer', 'item_type', 'created_by')

    # Filters
    status = request.GET.get('status', '')
    priority = request.GET.get('priority', '')
    customer_id = request.GET.get('customer', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    search = request.GET.get('q', '').strip()

    if status:
        qs = qs.filter(status=status)
    if priority:
        qs = qs.filter(priority=priority)
    if customer_id:
        qs = qs.filter(customer_id=customer_id)
    if date_from:
        qs = qs.filter(order_date__gte=date_from)
    if date_to:
        qs = qs.filter(order_date__lte=date_to)
    if search:
        qs = qs.filter(
            Q(order_number__icontains=search) |
            Q(customer__name__icontains=search) |
            Q(description__icontains=search)
        )

    customers = Customer.objects.filter(is_active=True).order_by('name')

    from .models import ORDER_STATUS_CHOICES, PRIORITY_CHOICES
    context = {
        'orders': qs,
        'customers': customers,
        'order_status_choices': ORDER_STATUS_CHOICES,
        'priority_choices': PRIORITY_CHOICES,
        'current_filters': {
            'status': status,
            'priority': priority,
            'customer': customer_id,
            'date_from': date_from,
            'date_to': date_to,
            'q': search,
        },
    }
    return render(request, 'orders/order_list.html', context)


# ---------------------------------------------------------------------------
# Order Create
# ---------------------------------------------------------------------------

@supervisor_or_above
def order_create(request):
    """Create a new job order. Supervisor+ only."""
    if request.method == 'POST':
        form = JobOrderForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.created_by = request.user
            order.save()
            messages.success(
                request,
                f'Job order {order.order_number} created successfully.'
            )
            # Warn if required metal/purity is not in stock
            in_stock, warning = _check_metal_stock(order)
            if warning:
                messages.warning(request, warning)
            return redirect('orders:order_detail', pk=order.pk)
    else:
        form = JobOrderForm()

    return render(request, 'orders/order_form.html', {
        'form': form,
        'title': 'Create Job Order',
        'action': 'Create',
    })


# ---------------------------------------------------------------------------
# Order Detail
# ---------------------------------------------------------------------------

@login_required
def order_detail(request, pk):
    """Full detail view of a job order, including notes and linked production job."""
    order = get_object_or_404(
        JobOrder.objects.select_related('customer', 'item_type', 'created_by'),
        pk=pk,
    )
    notes = order.notes.select_related('added_by').order_by('-created_at')
    production_jobs = order.production_jobs.select_related(
        'current_stage', 'created_by'
    ) if hasattr(order, 'production_jobs') else []

    note_form = OrderNoteForm()

    if request.method == 'POST' and 'add_note' in request.POST:
        note_form = OrderNoteForm(request.POST)
        if note_form.is_valid():
            note = note_form.save(commit=False)
            note.order = order
            note.added_by = request.user
            note.save()
            messages.success(request, 'Note added.')
            return redirect('orders:order_detail', pk=order.pk)

    context = {
        'order': order,
        'notes': notes,
        'note_form': note_form,
        'production_jobs': production_jobs,
        'today': timezone.now().date(),
    }
    return render(request, 'orders/order_detail.html', context)


# ---------------------------------------------------------------------------
# Order Delete (admin only)
# ---------------------------------------------------------------------------

@login_required
def order_delete(request, pk):
    """Permanently delete a job order and all its linked production jobs. Admin only."""
    if request.user.role != ROLE_ADMIN:
        return HttpResponseForbidden('<h1>403 Forbidden</h1><p>Admin access required.</p>')

    order = get_object_or_404(JobOrder, pk=pk)

    if request.method == 'POST':
        order_number = order.order_number
        with transaction.atomic():
            # Explicitly delete linked production jobs (SET_NULL wouldn't remove them)
            linked_jobs = order.production_jobs.all()
            job_count = linked_jobs.count()
            linked_jobs.delete()
            order.delete()
        messages.success(
            request,
            f'Order {order_number} and {job_count} linked production job(s) permanently deleted.',
        )
        return redirect('orders:order_list')

    linked_jobs = order.production_jobs.select_related('current_stage').order_by('job_number')
    return render(request, 'orders/order_confirm_delete.html', {
        'order': order,
        'linked_jobs': linked_jobs,
    })


# ---------------------------------------------------------------------------
# Order Edit
# ---------------------------------------------------------------------------

@supervisor_or_above
def order_edit(request, pk):
    """Edit an existing job order."""
    order = get_object_or_404(JobOrder, pk=pk)

    if order.status in (STATUS_DELIVERED, STATUS_CANCELLED):
        messages.warning(
            request,
            f'Order {order.order_number} cannot be edited — it is {order.get_status_display()}.'
        )
        return redirect('orders:order_detail', pk=order.pk)

    if request.method == 'POST':
        form = JobOrderForm(request.POST, instance=order)
        if form.is_valid():
            form.save()
            messages.success(request, f'Order {order.order_number} updated.')
            return redirect('orders:order_detail', pk=order.pk)
    else:
        form = JobOrderForm(instance=order)

    return render(request, 'orders/order_form.html', {
        'form': form,
        'order': order,
        'title': f'Edit Order {order.order_number}',
        'action': 'Save Changes',
    })


# ---------------------------------------------------------------------------
# Update Order Status
# ---------------------------------------------------------------------------

@supervisor_or_above
def update_order_status(request, pk):
    """Quick status update for a job order, optionally adding a note."""
    order = get_object_or_404(JobOrder, pk=pk)

    if request.method == 'POST':
        form = OrderStatusUpdateForm(request.POST)
        if form.is_valid():
            old_status = order.get_status_display()
            order.status = form.cleaned_data['status']
            order.save(update_fields=['status', 'updated_at'])

            note_text = form.cleaned_data.get('note', '').strip()
            auto_note = (
                f'Status changed from "{old_status}" to '
                f'"{order.get_status_display()}".'
            )
            if note_text:
                auto_note = f'{auto_note} {note_text}'

            OrderNote.objects.create(
                order=order,
                note=auto_note,
                added_by=request.user,
            )
            messages.success(
                request,
                f'Order {order.order_number} status updated to '
                f'{order.get_status_display()}.'
            )
            return redirect('orders:order_detail', pk=order.pk)
    else:
        form = OrderStatusUpdateForm(initial={'status': order.status})

    return render(request, 'orders/order_status_update.html', {
        'form': form,
        'order': order,
    })


# ---------------------------------------------------------------------------
# Order Delivery
# ---------------------------------------------------------------------------

@supervisor_or_above
def order_delivery(request, pk):
    """Mark an order as delivered, recording actual weight and cost."""
    order = get_object_or_404(JobOrder, pk=pk)

    if order.status == STATUS_DELIVERED:
        messages.info(request, f'Order {order.order_number} is already marked as delivered.')
        return redirect('orders:order_detail', pk=order.pk)

    if request.method == 'POST':
        form = OrderDeliveryForm(request.POST, instance=order)
        if form.is_valid():
            delivery = form.save(commit=False)
            delivery.status = STATUS_DELIVERED
            if not delivery.delivery_date:
                delivery.delivery_date = timezone.now().date()
            delivery.save()

            OrderNote.objects.create(
                order=order,
                note=(
                    f'Order delivered on {delivery.delivery_date}. '
                    f'Actual weight: {delivery.actual_weight}g. '
                    f'Actual cost: {delivery.actual_cost}.'
                ),
                added_by=request.user,
            )
            messages.success(
                request,
                f'Order {order.order_number} marked as delivered.'
            )
            return redirect('orders:order_detail', pk=order.pk)
    else:
        form = OrderDeliveryForm(instance=order)

    return render(request, 'orders/order_delivery.html', {
        'form': form,
        'order': order,
    })


# ---------------------------------------------------------------------------
# Customer List
# ---------------------------------------------------------------------------

@login_required
def customer_list(request):
    """List all customers with optional search."""
    qs = Customer.objects.all()
    search = request.GET.get('q', '').strip()
    if search:
        qs = qs.filter(
            Q(name__icontains=search) |
            Q(phone__icontains=search) |
            Q(email__icontains=search)
        )
    show_inactive = request.GET.get('show_inactive', '')
    if not show_inactive:
        qs = qs.filter(is_active=True)

    return render(request, 'orders/customer_list.html', {
        'customers': qs,
        'search': search,
        'show_inactive': show_inactive,
    })


# ---------------------------------------------------------------------------
# Customer Create
# ---------------------------------------------------------------------------

@supervisor_or_above
def customer_create(request):
    """Create a new customer."""
    if request.method == 'POST':
        form = CustomerForm(request.POST)
        if form.is_valid():
            customer = form.save()
            messages.success(request, f'Customer "{customer.name}" created.')
            return redirect('orders:customer_detail', pk=customer.pk)
    else:
        form = CustomerForm()

    return render(request, 'orders/customer_form.html', {
        'form': form,
        'title': 'Add Customer',
        'action': 'Create',
    })


# ---------------------------------------------------------------------------
# Customer Edit
# ---------------------------------------------------------------------------

@supervisor_or_above
def customer_edit(request, pk):
    """Edit an existing customer."""
    customer = get_object_or_404(Customer, pk=pk)

    if request.method == 'POST':
        form = CustomerForm(request.POST, instance=customer)
        if form.is_valid():
            form.save()
            messages.success(request, f'Customer "{customer.name}" updated.')
            return redirect('orders:customer_detail', pk=customer.pk)
    else:
        form = CustomerForm(instance=customer)

    return render(request, 'orders/customer_form.html', {
        'form': form,
        'customer': customer,
        'title': f'Edit {customer.name}',
        'action': 'Save Changes',
    })


# ---------------------------------------------------------------------------
# Customer Detail
# ---------------------------------------------------------------------------

@login_required
def customer_detail(request, pk):
    """Detail view for a customer, showing their job order history."""
    customer = get_object_or_404(Customer, pk=pk)
    orders = customer.job_orders.select_related('item_type').order_by('-created_at')

    return render(request, 'orders/customer_detail.html', {
        'customer': customer,
        'orders': orders,
    })
