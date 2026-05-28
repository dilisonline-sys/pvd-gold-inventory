from django.contrib import admin

from .models import (
    FinalProduct,
    MaterialIssuance,
    ProcessRecord,
    ProcessStage,
    ProductionJob,
    QualityCheck,
)


# ---------------------------------------------------------------------------
# ProcessStage
# ---------------------------------------------------------------------------

@admin.register(ProcessStage)
class ProcessStageAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'name', 'code', 'is_active')
    list_display_links = ('order_number', 'name')
    list_editable = ('is_active',)
    list_filter = ('is_active',)
    search_fields = ('name', 'code', 'description')
    ordering = ('order_number',)
    readonly_fields = ('code',)


# ---------------------------------------------------------------------------
# ProcessRecord inline for ProductionJob
# ---------------------------------------------------------------------------

class ProcessRecordInline(admin.TabularInline):
    model = ProcessRecord
    extra = 0
    readonly_fields = ('started_at', 'completed_at')
    fields = (
        'stage',
        'status',
        'assigned_to',
        'weight_in',
        'weight_out',
        'waste_weight',
        'started_at',
        'completed_at',
    )
    show_change_link = True


class MaterialIssuanceInline(admin.TabularInline):
    model = MaterialIssuance
    extra = 0
    readonly_fields = ('issued_at', 'issued_by')
    fields = ('material', 'stage', 'quantity_requested', 'quantity_issued', 'issued_by', 'issued_at', 'notes')


# ---------------------------------------------------------------------------
# ProductionJob
# ---------------------------------------------------------------------------

@admin.register(ProductionJob)
class ProductionJobAdmin(admin.ModelAdmin):
    list_display = (
        'job_number',
        'title',
        'current_stage',
        'status',
        'priority',
        'target_completion_date',
        'created_by',
        'created_at',
    )
    list_filter = ('status', 'priority', 'current_stage')
    search_fields = ('job_number', 'title', 'description')
    readonly_fields = ('job_number', 'created_at', 'updated_at')
    raw_id_fields = ('created_by', 'job_order')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    inlines = [ProcessRecordInline, MaterialIssuanceInline]

    fieldsets = (
        ('Job Information', {
            'fields': ('job_number', 'job_order', 'title', 'description'),
        }),
        ('Status & Progress', {
            'fields': ('current_stage', 'status', 'priority'),
        }),
        ('Dates', {
            'fields': ('target_completion_date', 'actual_completion_date', 'created_at', 'updated_at'),
        }),
        ('Ownership', {
            'fields': ('created_by',),
        }),
    )


# ---------------------------------------------------------------------------
# ProcessRecord
# ---------------------------------------------------------------------------

class QualityCheckInline(admin.TabularInline):
    model = QualityCheck
    extra = 0
    readonly_fields = ('checked_at', 'checked_by')
    fields = ('checked_by', 'checked_at', 'result', 'finish_grade', 'weight', 'approved_by')
    show_change_link = True


@admin.register(ProcessRecord)
class ProcessRecordAdmin(admin.ModelAdmin):
    list_display = (
        'production_job',
        'stage',
        'status',
        'assigned_to',
        'started_at',
        'completed_at',
        'weight_in',
        'weight_out',
    )
    list_filter = ('status', 'stage')
    search_fields = ('production_job__job_number', 'notes', 'remarks')
    raw_id_fields = ('production_job', 'assigned_to')
    readonly_fields = ('started_at', 'completed_at')
    ordering = ('production_job', 'stage__order_number')
    inlines = [QualityCheckInline]


# ---------------------------------------------------------------------------
# MaterialIssuance
# ---------------------------------------------------------------------------

@admin.register(MaterialIssuance)
class MaterialIssuanceAdmin(admin.ModelAdmin):
    list_display = (
        'production_job',
        'material',
        'stage',
        'quantity_requested',
        'quantity_issued',
        'issued_by',
        'issued_at',
    )
    list_filter = ('stage',)
    search_fields = ('production_job__job_number', 'material__name', 'notes')
    raw_id_fields = ('production_job', 'issued_by')
    readonly_fields = ('issued_at',)
    date_hierarchy = 'issued_at'
    ordering = ('-issued_at',)


# ---------------------------------------------------------------------------
# QualityCheck
# ---------------------------------------------------------------------------

@admin.register(QualityCheck)
class QualityCheckAdmin(admin.ModelAdmin):
    list_display = (
        'process_record',
        'checked_by',
        'checked_at',
        'result',
        'finish_grade',
        'approved_by',
    )
    list_filter = ('result', 'finish_grade')
    search_fields = (
        'process_record__production_job__job_number',
        'defects_found',
        'corrective_action',
    )
    raw_id_fields = ('process_record', 'checked_by', 'approved_by')
    readonly_fields = ('checked_at',)
    date_hierarchy = 'checked_at'
    ordering = ('-checked_at',)


@admin.register(FinalProduct)
class FinalProductAdmin(admin.ModelAdmin):
    list_display = ('production_job', 'name', 'metal_type', 'purity', 'final_weight', 'finish', 'created_at')
    list_filter = ('finish', 'metal_type')
    search_fields = ('production_job__job_number', 'name', 'hallmark')
    readonly_fields = ('created_at', 'created_by')
