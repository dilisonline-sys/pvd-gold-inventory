from django.contrib import admin

from .models import (
    CurrentStock,
    MaterialCategory,
    RawMaterial,
    StockEntry,
    StockTransaction,
    Supplier,
)


# ---------------------------------------------------------------------------
# MaterialCategory
# ---------------------------------------------------------------------------

@admin.register(MaterialCategory)
class MaterialCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)


# ---------------------------------------------------------------------------
# RawMaterial
# ---------------------------------------------------------------------------

@admin.register(RawMaterial)
class RawMaterialAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'category',
        'unit_of_measure',
        'minimum_stock_level',
        'current_qty',
        'is_active',
        'created_at',
    )
    list_filter = ('category', 'unit_of_measure', 'is_active')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at',)
    ordering = ('category', 'name')

    @admin.display(description='Stock on Hand')
    def current_qty(self, obj):
        return obj.get_current_stock()


# ---------------------------------------------------------------------------
# Supplier
# ---------------------------------------------------------------------------

@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('name', 'contact_person', 'phone', 'email', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'contact_person', 'email')


# ---------------------------------------------------------------------------
# StockEntry
# ---------------------------------------------------------------------------

@admin.register(StockEntry)
class StockEntryAdmin(admin.ModelAdmin):
    list_display = (
        'material',
        'supplier',
        'quantity',
        'unit_cost',
        'total_cost',
        'purity',
        'entry_date',
        'batch_number',
        'is_bulk',
        'entered_by',
    )
    list_filter = ('entry_date', 'is_bulk', 'material__category')
    search_fields = ('material__name', 'batch_number', 'supplier__name')
    readonly_fields = ('total_cost',)
    date_hierarchy = 'entry_date'
    ordering = ('-entry_date', '-id')
    raw_id_fields = ('material', 'supplier', 'entered_by')


# ---------------------------------------------------------------------------
# StockTransaction
# ---------------------------------------------------------------------------

@admin.register(StockTransaction)
class StockTransactionAdmin(admin.ModelAdmin):
    list_display = (
        'material',
        'transaction_type',
        'quantity',
        'reference_number',
        'job_order',
        'created_by',
        'created_at',
    )
    list_filter = ('transaction_type', 'created_at', 'material__category')
    search_fields = ('material__name', 'reference_number', 'notes')
    readonly_fields = ('created_at',)
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    raw_id_fields = ('material', 'created_by', 'job_order')


# ---------------------------------------------------------------------------
# CurrentStock
# ---------------------------------------------------------------------------

@admin.register(CurrentStock)
class CurrentStockAdmin(admin.ModelAdmin):
    list_display = ('material', 'quantity_on_hand', 'unit', 'last_updated', 'is_low')
    search_fields = ('material__name',)
    readonly_fields = ('last_updated',)
    ordering = ('material__category', 'material__name')

    @admin.display(description='Unit')
    def unit(self, obj):
        return obj.material.get_unit_of_measure_display()

    @admin.display(description='Low Stock?', boolean=True)
    def is_low(self, obj):
        return obj.material.is_low_stock
