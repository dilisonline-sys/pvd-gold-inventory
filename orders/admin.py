from django.contrib import admin

from .models import Customer, ItemType, JobOrder, OrderNote


# ---------------------------------------------------------------------------
# Inlines
# ---------------------------------------------------------------------------

class OrderNoteInline(admin.TabularInline):
    model = OrderNote
    extra = 0
    readonly_fields = ('added_by', 'created_at')
    fields = ('note', 'added_by', 'created_at')

    def has_add_permission(self, request, obj=None):
        return False


# ---------------------------------------------------------------------------
# CustomerAdmin
# ---------------------------------------------------------------------------

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'email', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name', 'phone', 'email')
    ordering = ('name',)


# ---------------------------------------------------------------------------
# ItemTypeAdmin
# ---------------------------------------------------------------------------

@admin.register(ItemType)
class ItemTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    ordering = ('name',)


# ---------------------------------------------------------------------------
# JobOrderAdmin
# ---------------------------------------------------------------------------

@admin.register(JobOrder)
class JobOrderAdmin(admin.ModelAdmin):
    list_display = (
        'order_number', 'customer', 'item_type', 'metal_type', 'metal_purity',
        'status', 'priority', 'order_date', 'required_date', 'estimated_cost',
    )
    list_filter = ('status', 'priority', 'metal_type', 'metal_purity')
    search_fields = ('order_number', 'customer__name', 'description')
    ordering = ('-created_at',)
    readonly_fields = ('order_number', 'created_by', 'created_at', 'updated_at', 'balance_due')
    inlines = [OrderNoteInline]

    fieldsets = (
        ('Order Info', {
            'fields': ('order_number', 'customer', 'item_type', 'status', 'priority'),
        }),
        ('Item Details', {
            'fields': (
                'description', 'quantity', 'metal_type', 'metal_purity',
                'estimated_weight', 'actual_weight',
                'stone_type', 'stone_weight', 'special_instructions',
            ),
        }),
        ('Dates', {
            'fields': ('order_date', 'required_date', 'delivery_date'),
        }),
        ('Financials', {
            'fields': ('estimated_cost', 'actual_cost', 'advance_payment', 'balance_due'),
        }),
        ('Audit', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


# ---------------------------------------------------------------------------
# OrderNoteAdmin
# ---------------------------------------------------------------------------

@admin.register(OrderNote)
class OrderNoteAdmin(admin.ModelAdmin):
    list_display = ('order', 'added_by', 'created_at', 'note_preview')
    search_fields = ('order__order_number', 'note')
    ordering = ('-created_at',)
    readonly_fields = ('added_by', 'created_at')

    def note_preview(self, obj):
        return obj.note[:80] + '…' if len(obj.note) > 80 else obj.note
    note_preview.short_description = 'Note'
