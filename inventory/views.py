import csv
import io
from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from accounts.decorators import role_required, supervisor_or_above
from accounts.models import (
    ROLE_ADMIN,
    ROLE_INVENTORY_CLERK,
    ROLE_MANAGER,
    ROLE_SUPERVISOR,
)

from .forms import (
    ADJUSTMENT_ADD,
    ADJUSTMENT_SET,
    ADJUSTMENT_SUBTRACT,
    BulkStockEntryForm,
    MaterialForm,
    StockAdjustmentForm,
    StockEntryForm,
    SupplierForm,
)
from .models import (
    CurrentStock,
    RawMaterial,
    StockEntry,
    StockTransaction,
    Supplier,
    TRANSACTION_ADJUSTMENT,
    TRANSACTION_IN,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _update_current_stock(material, delta):
    """Add *delta* (positive or negative Decimal) to CurrentStock for *material*.

    Creates the CurrentStock row if it doesn't exist yet.
    """
    stock, _ = CurrentStock.objects.get_or_create(
        material=material,
        defaults={'quantity_on_hand': Decimal('0')},
    )
    stock.quantity_on_hand += delta
    stock.save()


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

@login_required
def dashboard(request):
    """Overview: total materials, low-stock count, recent transactions."""
    total_materials = RawMaterial.objects.filter(is_active=True).count()

    low_stock_materials = [
        m for m in RawMaterial.objects.filter(is_active=True).select_related('category', 'current_stock')
        if m.is_low_stock
    ]

    recent_transactions = (
        StockTransaction.objects
        .select_related('material', 'created_by')
        .order_by('-created_at')[:10]
    )

    recent_entries = (
        StockEntry.objects
        .select_related('material', 'supplier', 'entered_by')
        .order_by('-entry_date', '-id')[:10]
    )

    context = {
        'total_materials': total_materials,
        'low_stock_count': len(low_stock_materials),
        'low_stock_materials': low_stock_materials[:5],
        'recent_transactions': recent_transactions,
        'recent_entries': recent_entries,
    }
    return render(request, 'inventory/dashboard.html', context)


# ---------------------------------------------------------------------------
# Materials
# ---------------------------------------------------------------------------

@login_required
def material_list(request):
    """List all materials with their current stock levels."""
    materials = (
        RawMaterial.objects
        .select_related('category', 'current_stock')
        .order_by('category__name', 'name')
    )

    # Optional search
    search = request.GET.get('search', '').strip()
    if search:
        materials = materials.filter(
            Q(name__icontains=search) | Q(category__name__icontains=search)
        )

    # Optional category filter
    category_filter = request.GET.get('category', '').strip()
    if category_filter:
        materials = materials.filter(category__name=category_filter)

    # Optional active filter
    active_filter = request.GET.get('active', 'true')
    if active_filter == 'true':
        materials = materials.filter(is_active=True)
    elif active_filter == 'false':
        materials = materials.filter(is_active=False)

    from .models import MaterialCategory
    categories = MaterialCategory.objects.all()

    context = {
        'materials': materials,
        'categories': categories,
        'search': search,
        'category_filter': category_filter,
        'active_filter': active_filter,
    }
    return render(request, 'inventory/material_list.html', context)


@login_required
@role_required(ROLE_ADMIN, ROLE_MANAGER, ROLE_SUPERVISOR, ROLE_INVENTORY_CLERK)
def material_create(request):
    """Create a new raw material."""
    if request.method == 'POST':
        form = MaterialForm(request.POST)
        if form.is_valid():
            material = form.save()
            messages.success(request, f'Material "{material.name}" created successfully.')
            return redirect('inventory:material_list')
    else:
        form = MaterialForm()

    return render(request, 'inventory/material_form.html', {'form': form, 'action': 'Create'})


@login_required
@role_required(ROLE_ADMIN, ROLE_MANAGER, ROLE_SUPERVISOR, ROLE_INVENTORY_CLERK)
def material_edit(request, pk):
    """Edit an existing raw material."""
    material = get_object_or_404(RawMaterial, pk=pk)

    if request.method == 'POST':
        form = MaterialForm(request.POST, instance=material)
        if form.is_valid():
            form.save()
            messages.success(request, f'Material "{material.name}" updated successfully.')
            return redirect('inventory:material_list')
    else:
        form = MaterialForm(instance=material)

    return render(
        request,
        'inventory/material_form.html',
        {'form': form, 'action': 'Edit', 'material': material},
    )


# ---------------------------------------------------------------------------
# Stock Entries
# ---------------------------------------------------------------------------

@login_required
@role_required(ROLE_ADMIN, ROLE_MANAGER, ROLE_SUPERVISOR, ROLE_INVENTORY_CLERK)
def stock_entry(request):
    """Record a single stock-in entry and update CurrentStock."""
    if request.method == 'POST':
        form = StockEntryForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                entry = form.save(commit=False)
                entry.entered_by = request.user
                entry.save()

                # Create a corresponding StockTransaction record
                StockTransaction.objects.create(
                    material=entry.material,
                    transaction_type=TRANSACTION_IN,
                    quantity=entry.quantity,
                    reference_number=entry.batch_number,
                    notes=entry.notes,
                    created_by=request.user,
                )

                # Update CurrentStock
                _update_current_stock(entry.material, entry.quantity)

            messages.success(
                request,
                f'Stock entry recorded: {entry.quantity} {entry.material.unit_of_measure} '
                f'of {entry.material.name}.',
            )
            return redirect('inventory:stock_history')
    else:
        form = StockEntryForm()

    return render(request, 'inventory/stock_entry.html', {'form': form})


@login_required
@role_required(ROLE_ADMIN, ROLE_MANAGER, ROLE_SUPERVISOR, ROLE_INVENTORY_CLERK)
def bulk_stock_entry(request):
    """Upload a CSV file to create multiple StockEntry records at once.

    CSV columns: material_name, quantity, unit_cost, supplier_name,
                 batch_number, purity, notes
    """
    import csv as csv_module
    from django.http import HttpResponse

    # Handle sample CSV download
    if request.method == 'GET' and request.GET.get('download_sample'):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="bulk_stock_sample.csv"'
        writer = csv_module.writer(response)
        writer.writerow(['material_name', 'quantity', 'unit_cost', 'supplier_name', 'batch_number', 'purity', 'notes'])
        writer.writerow(['Gold 18K', '100.5', '85.00', 'Gold Suppliers Ltd', 'BATCH-001', '18K', '18 karat gold alloy'])
        writer.writerow(['Silver 925', '500.0', '1.20', 'Silver Imports Co', 'BATCH-002', '925', 'Sterling silver'])
        writer.writerow(['Diamond Round 1ct', '25', '500.00', 'Gem House', 'GEM-001', '', 'Round brilliant cut'])
        return response

    results = None  # list of per-row outcome dicts populated after processing

    if request.method == 'POST':
        form = BulkStockEntryForm(request.POST, request.FILES)
        if form.is_valid():
            rows = form.get_parsed_rows()
            category_filter = form.cleaned_data.get('material_category')

            created_count = 0
            skipped_rows = []

            with transaction.atomic():
                for i, row in enumerate(rows, start=2):
                    material_name = row['material_name']
                    material_qs = RawMaterial.objects.filter(
                        name__iexact=material_name,
                        is_active=True,
                    )
                    if category_filter:
                        material_qs = material_qs.filter(category=category_filter)

                    material = material_qs.first()
                    if material is None:
                        skipped_rows.append(
                            f'Row {i}: material "{material_name}" not found'
                            + (f' in category "{category_filter}".' if category_filter else '.')
                        )
                        continue

                    # Resolve supplier (optional)
                    supplier = None
                    supplier_name = row.get('supplier_name', '').strip()
                    if supplier_name:
                        supplier = Supplier.objects.filter(
                            name__iexact=supplier_name, is_active=True
                        ).first()
                        if supplier is None:
                            skipped_rows.append(
                                f'Row {i}: supplier "{supplier_name}" not found; '
                                f'entry for "{material_name}" skipped.'
                            )
                            continue

                    quantity = Decimal(str(row['quantity']))
                    unit_cost = Decimal(str(row['unit_cost']))
                    batch_number = row.get('batch_number', '')
                    purity = row.get('purity', '')
                    notes = row.get('notes', '')

                    entry = StockEntry.objects.create(
                        material=material,
                        supplier=supplier,
                        quantity=quantity,
                        unit_cost=unit_cost,
                        entry_date=timezone.now().date(),
                        batch_number=batch_number,
                        purity=purity,
                        notes=notes,
                        entered_by=request.user,
                        is_bulk=True,
                    )

                    StockTransaction.objects.create(
                        material=material,
                        transaction_type=TRANSACTION_IN,
                        quantity=quantity,
                        reference_number=batch_number,
                        notes=notes,
                        created_by=request.user,
                    )

                    _update_current_stock(material, quantity)
                    created_count += 1

            results = {
                'created': created_count,
                'skipped': skipped_rows,
                'total_rows': len(rows),
            }

            if created_count:
                messages.success(
                    request,
                    f'Bulk upload complete: {created_count} entries created'
                    + (f', {len(skipped_rows)} rows skipped.' if skipped_rows else '.'),
                )
            else:
                messages.warning(request, 'No entries were created. Check skipped rows below.')

            # Render the same page with results summary
            form = BulkStockEntryForm()  # fresh form for another upload
    else:
        form = BulkStockEntryForm()

    return render(
        request,
        'inventory/bulk_stock_entry.html',
        {'form': form, 'results': results},
    )


# ---------------------------------------------------------------------------
# Stock History
# ---------------------------------------------------------------------------

@login_required
def stock_history(request):
    """List StockTransactions with optional filters."""
    transactions_qs = (
        StockTransaction.objects
        .select_related('material', 'material__category', 'created_by', 'job_order')
        .order_by('-created_at')
    )

    # Filters
    material_filter = request.GET.get('material', '').strip()
    type_filter = request.GET.get('transaction_type', '').strip()
    date_from = request.GET.get('date_from', '').strip()
    date_to = request.GET.get('date_to', '').strip()
    search = request.GET.get('search', '').strip()

    if material_filter:
        transactions_qs = transactions_qs.filter(material__id=material_filter)
    if type_filter:
        transactions_qs = transactions_qs.filter(transaction_type=type_filter)
    if date_from:
        transactions_qs = transactions_qs.filter(created_at__date__gte=date_from)
    if date_to:
        transactions_qs = transactions_qs.filter(created_at__date__lte=date_to)
    if search:
        transactions_qs = transactions_qs.filter(
            Q(material__name__icontains=search)
            | Q(reference_number__icontains=search)
            | Q(notes__icontains=search)
        )

    from .models import TRANSACTION_TYPE_CHOICES
    materials = RawMaterial.objects.filter(is_active=True).order_by('name')

    context = {
        'transactions': transactions_qs,
        'materials': materials,
        'transaction_type_choices': TRANSACTION_TYPE_CHOICES,
        'material_filter': material_filter,
        'type_filter': type_filter,
        'date_from': date_from,
        'date_to': date_to,
        'search': search,
    }
    return render(request, 'inventory/stock_history.html', context)


# ---------------------------------------------------------------------------
# Stock Adjustment
# ---------------------------------------------------------------------------

@login_required
@supervisor_or_above
def stock_adjustment(request):
    """Manual stock adjustment – restricted to supervisor and above."""
    if request.method == 'POST':
        form = StockAdjustmentForm(request.POST)
        if form.is_valid():
            material = form.cleaned_data['material']
            mode = form.cleaned_data['adjustment_mode']
            qty = form.cleaned_data['quantity']
            reference_number = form.cleaned_data.get('reference_number', '')
            notes = form.cleaned_data.get('notes', '')

            with transaction.atomic():
                stock, _ = CurrentStock.objects.get_or_create(
                    material=material,
                    defaults={'quantity_on_hand': Decimal('0')},
                )
                old_qty = stock.quantity_on_hand

                if mode == ADJUSTMENT_ADD:
                    delta = qty
                    stock.quantity_on_hand += qty
                elif mode == ADJUSTMENT_SUBTRACT:
                    delta = -qty
                    stock.quantity_on_hand -= qty
                else:  # ADJUSTMENT_SET
                    delta = qty - old_qty
                    stock.quantity_on_hand = qty

                stock.save()

                StockTransaction.objects.create(
                    material=material,
                    transaction_type=TRANSACTION_ADJUSTMENT,
                    quantity=abs(delta),
                    reference_number=reference_number,
                    notes=(
                        f'[{mode.upper()}] old={old_qty}, new={stock.quantity_on_hand}. '
                        + notes
                    ).strip(),
                    created_by=request.user,
                )

            messages.success(
                request,
                f'Stock for "{material.name}" adjusted from {old_qty} to '
                f'{stock.quantity_on_hand} {material.unit_of_measure}.',
            )
            return redirect('inventory:stock_history')
    else:
        form = StockAdjustmentForm()

    return render(request, 'inventory/stock_adjustment.html', {'form': form})


# ---------------------------------------------------------------------------
# Suppliers
# ---------------------------------------------------------------------------

@login_required
def supplier_list(request):
    """List all suppliers."""
    suppliers = Supplier.objects.all().order_by('name')

    active_filter = request.GET.get('active', 'true')
    if active_filter == 'true':
        suppliers = suppliers.filter(is_active=True)
    elif active_filter == 'false':
        suppliers = suppliers.filter(is_active=False)

    search = request.GET.get('search', '').strip()
    if search:
        suppliers = suppliers.filter(
            Q(name__icontains=search) | Q(contact_person__icontains=search)
        )

    context = {
        'suppliers': suppliers,
        'active_filter': active_filter,
        'search': search,
    }
    return render(request, 'inventory/supplier_list.html', context)


@login_required
@role_required(ROLE_ADMIN, ROLE_MANAGER, ROLE_SUPERVISOR, ROLE_INVENTORY_CLERK)
def supplier_create(request):
    """Create a new supplier."""
    if request.method == 'POST':
        form = SupplierForm(request.POST)
        if form.is_valid():
            supplier = form.save()
            messages.success(request, f'Supplier "{supplier.name}" created successfully.')
            return redirect('inventory:supplier_list')
    else:
        form = SupplierForm()

    return render(
        request,
        'inventory/supplier_form.html',
        {'form': form, 'action': 'Create'},
    )


@login_required
@role_required(ROLE_ADMIN, ROLE_MANAGER, ROLE_SUPERVISOR, ROLE_INVENTORY_CLERK)
def supplier_edit(request, pk):
    """Edit an existing supplier."""
    supplier = get_object_or_404(Supplier, pk=pk)

    if request.method == 'POST':
        form = SupplierForm(request.POST, instance=supplier)
        if form.is_valid():
            form.save()
            messages.success(request, f'Supplier "{supplier.name}" updated successfully.')
            return redirect('inventory:supplier_list')
    else:
        form = SupplierForm(instance=supplier)

    return render(
        request,
        'inventory/supplier_form.html',
        {'form': form, 'action': 'Edit', 'supplier': supplier},
    )


# ---------------------------------------------------------------------------
# Low Stock Alerts
# ---------------------------------------------------------------------------

@login_required
def low_stock_alerts(request):
    """Show all materials whose current stock is below the minimum level."""
    active_materials = (
        RawMaterial.objects
        .filter(is_active=True)
        .select_related('category', 'current_stock')
        .order_by('category__name', 'name')
    )

    low_stock = [m for m in active_materials if m.is_low_stock]

    context = {
        'low_stock_materials': low_stock,
        'count': len(low_stock),
    }
    return render(request, 'inventory/low_stock_alerts.html', context)
