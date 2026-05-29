from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Count, Q
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from accounts.decorators import supervisor_or_above
from accounts.models import (
    ROLE_ADMIN,
    ROLE_MANAGER,
    ROLE_SUPERVISOR,
    ROLE_PRODUCTION_WORKER,
)

from .forms import (
    CatalogBulkUploadForm,
    FinalProductForm,
    MaterialIssuanceForm,
    MaterialRequirementForm,
    ProcessRecordForm,
    ProductionJobForm,
    QualityCheckForm,
    StageAdvanceForm,
)
from .models import (
    FinalProduct,
    JOB_STATUS_CHOICES,
    PRIORITY_CHOICES,
    RECORD_STATUS_IN_PROGRESS,
    RECORD_STATUS_PENDING,
    STATUS_COMPLETED,
    STATUS_IN_PROGRESS,
    MaterialIssuance,
    MaterialRequirement,
    ProcessRecord,
    ProcessStage,
    ProductionJob,
    QualityCheck,
)

User = get_user_model()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _is_supervisor_or_above(user):
    return user.role in (ROLE_ADMIN, ROLE_MANAGER, ROLE_SUPERVISOR)


def _get_or_create_process_record(job, stage):
    """Return the ProcessRecord for a job/stage pair, creating it if absent."""
    record, _ = ProcessRecord.objects.get_or_create(
        production_job=job,
        stage=stage,
        defaults={'status': RECORD_STATUS_PENDING},
    )
    return record


# ---------------------------------------------------------------------------
# Production Dashboard
# ---------------------------------------------------------------------------

@login_required
def production_dashboard(request):
    """Overview of all production jobs grouped by status and current stage."""
    jobs = (
        ProductionJob.objects
        .select_related('current_stage', 'created_by', 'job_order')
        .order_by('-created_at')
    )

    # Counts by status
    status_counts = {}
    for value, label in JOB_STATUS_CHOICES:
        status_counts[value] = jobs.filter(status=value).count()

    # Counts by stage — pass as list of dicts for template iteration
    stages = ProcessStage.objects.filter(is_active=True).order_by('order_number')
    stage_counts = [
        {'stage': stage, 'count': jobs.filter(current_stage=stage).count()}
        for stage in stages
    ]

    # Counts by priority
    priority_counts = {}
    for value, label in PRIORITY_CHOICES:
        priority_counts[value] = jobs.filter(priority=value).count()

    # Urgent/overdue jobs
    today = timezone.now().date()
    overdue_jobs = jobs.filter(
        target_completion_date__lt=today,
        status__in=[STATUS_IN_PROGRESS, 'PENDING'],
    )

    recent_jobs = jobs[:10]

    context = {
        'jobs': jobs,
        'recent_jobs': recent_jobs,
        'status_counts': status_counts,
        'stage_counts': stage_counts,
        'priority_counts': priority_counts,
        'stages': stages,
        'overdue_jobs': overdue_jobs,
        'total_jobs': jobs.count(),
        'job_status_choices': JOB_STATUS_CHOICES,
    }
    return render(request, 'manufacturing/production_dashboard.html', context)


# ---------------------------------------------------------------------------
# Stage Dashboard
# ---------------------------------------------------------------------------

@login_required
def stage_dashboard(request, stage_pk=None):
    """Show all production jobs currently at a given stage (or all stages)."""
    stages = ProcessStage.objects.filter(is_active=True).order_by('order_number')

    selected_stage = None
    if stage_pk:
        selected_stage = get_object_or_404(ProcessStage, pk=stage_pk, is_active=True)
        jobs = (
            ProductionJob.objects
            .filter(current_stage=selected_stage)
            .select_related('current_stage', 'created_by', 'job_order')
            .order_by('-updated_at')
        )
    else:
        jobs = (
            ProductionJob.objects
            .select_related('current_stage', 'created_by', 'job_order')
            .order_by('current_stage__order_number', '-updated_at')
        )

    # Build a grouped structure: {stage: [jobs]}
    stage_jobs = {}
    for stage in stages:
        stage_jobs[stage] = []
    for job in jobs:
        if job.current_stage in stage_jobs:
            stage_jobs[job.current_stage].append(job)

    context = {
        'stages': stages,
        'selected_stage': selected_stage,
        'stage_jobs': stage_jobs,
        'jobs': jobs,
    }
    return render(request, 'manufacturing/stage_dashboard.html', context)


# ---------------------------------------------------------------------------
# Job List
# ---------------------------------------------------------------------------

@login_required
def job_list(request):
    """List all production jobs with their current stage and status."""
    jobs = (
        ProductionJob.objects
        .select_related('current_stage', 'created_by', 'job_order')
        .order_by('-created_at')
    )

    # Optional filters
    status_filter = request.GET.get('status', '').strip()
    stage_filter = request.GET.get('stage', '').strip()
    priority_filter = request.GET.get('priority', '').strip()
    search = request.GET.get('q', '').strip()

    if status_filter:
        jobs = jobs.filter(status=status_filter)
    if stage_filter:
        jobs = jobs.filter(current_stage__pk=stage_filter)
    if priority_filter:
        jobs = jobs.filter(priority=priority_filter)
    if search:
        jobs = jobs.filter(
            Q(job_number__icontains=search)
            | Q(title__icontains=search)
            | Q(description__icontains=search)
        )

    from django.core.paginator import Paginator
    paginator = Paginator(jobs, 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    stages = ProcessStage.objects.filter(is_active=True).order_by('order_number')

    context = {
        'jobs': page_obj.object_list,
        'page_obj': page_obj,
        'stages': stages,
        'job_status_choices': JOB_STATUS_CHOICES,
        'priority_choices': PRIORITY_CHOICES,
        'status_filter': status_filter,
        'stage_filter': stage_filter,
        'priority_filter': priority_filter,
        'search': search,
    }
    return render(request, 'manufacturing/job_list.html', context)


# ---------------------------------------------------------------------------
# Job Create
# ---------------------------------------------------------------------------

@login_required
@supervisor_or_above
def job_create(request):
    """Create a new production job. Supervisor and above only."""
    if request.method == 'POST':
        form = ProductionJobForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                job = form.save(commit=False)
                job.created_by = request.user
                job.save()
                # Create the initial ProcessRecord for the starting stage
                _get_or_create_process_record(job, job.current_stage)
            messages.success(
                request,
                f'Production job {job.job_number} created successfully.',
            )
            return redirect('manufacturing:job_detail', pk=job.pk)
    else:
        form = ProductionJobForm()

    return render(
        request,
        'manufacturing/job_form.html',
        {'form': form, 'action': 'Create'},
    )


# ---------------------------------------------------------------------------
# Job Detail
# ---------------------------------------------------------------------------

@login_required
def job_detail(request, pk):
    """Full detail view with all stage process records and timeline."""
    job = get_object_or_404(
        ProductionJob.objects.select_related(
            'current_stage', 'created_by', 'job_order'
        ),
        pk=pk,
    )

    # All process records for this job ordered by stage sequence
    process_records = (
        job.process_records
        .select_related('stage', 'assigned_to')
        .order_by('stage__order_number')
    )

    # All QC records for this job
    qc_records = (
        QualityCheck.objects
        .filter(process_record__production_job=job)
        .select_related('checked_by', 'approved_by', 'process_record__stage')
        .order_by('-checked_at')
    )

    # Materials issued for this job
    issuances = (
        job.material_issuances
        .select_related('material', 'stage', 'issued_by')
        .order_by('-issued_at')
    )

    # Material requirements for this job with availability status
    requirements = (
        job.material_requirements
        .select_related('material', 'material__current_stock', 'material__category', 'created_by')
        .order_by('material__category__name', 'material__name')
    )
    requirement_form = MaterialRequirementForm()

    # Current stage record (create if missing)
    current_record = _get_or_create_process_record(job, job.current_stage)

    # All stages for timeline display
    all_stages = ProcessStage.objects.filter(is_active=True).order_by('order_number')

    # Build timeline: map stage -> record (or None)
    stage_record_map = {r.stage_id: r for r in process_records}
    timeline = []
    for stage in all_stages:
        record = stage_record_map.get(stage.pk)
        is_current = stage.pk == job.current_stage_id
        # Use actual record status; fall back to order-number for stages with no record
        if record is not None:
            is_completed = record.status in ('COMPLETED', 'SKIPPED')
        else:
            is_completed = (not is_current) and stage.order_number < job.current_stage.order_number
        timeline.append({
            'stage': stage,
            'record': record,
            'is_current': is_current,
            'is_completed': is_completed,
            'is_future': stage.order_number > job.current_stage.order_number,
        })

    can_manage = _is_supervisor_or_above(request.user)
    can_update = (
        can_manage
        or (
            request.user.role == ROLE_PRODUCTION_WORKER
            and current_record.assigned_to == request.user
        )
    )

    context = {
        'job': job,
        'process_records': process_records,
        'qc_records': qc_records,
        'issuances': issuances,
        'requirements': requirements,
        'requirement_form': requirement_form,
        'current_record': current_record,
        'timeline': timeline,
        'can_manage': can_manage,
        'can_update': can_update,
        'advance_form': StageAdvanceForm(),
    }
    return render(request, 'manufacturing/job_detail.html', context)


# ---------------------------------------------------------------------------
# Job Edit
# ---------------------------------------------------------------------------

@login_required
@supervisor_or_above
def job_edit(request, pk):
    """Edit an existing production job. Supervisor and above only."""
    job = get_object_or_404(ProductionJob, pk=pk)

    if request.method == 'POST':
        form = ProductionJobForm(request.POST, instance=job)
        if form.is_valid():
            updated_job = form.save()
            # Ensure a ProcessRecord exists for the (possibly new) current stage
            _get_or_create_process_record(updated_job, updated_job.current_stage)
            messages.success(
                request,
                f'Production job {job.job_number} updated successfully.',
            )
            return redirect('manufacturing:job_detail', pk=job.pk)
    else:
        form = ProductionJobForm(instance=job)

    return render(
        request,
        'manufacturing/job_form.html',
        {'form': form, 'action': 'Edit', 'job': job},
    )


# ---------------------------------------------------------------------------
# Job Delete (admin only)
# ---------------------------------------------------------------------------

@login_required
def job_delete(request, pk):
    """Permanently delete a production job. Admin only."""
    if request.user.role != ROLE_ADMIN:
        return HttpResponseForbidden('<h1>403 Forbidden</h1><p>Admin access required.</p>')

    job = get_object_or_404(ProductionJob, pk=pk)

    if request.method == 'POST':
        job_number = job.job_number
        job.delete()
        messages.success(request, f'Production job {job_number} has been permanently deleted.')
        return redirect('manufacturing:job_list')

    return render(request, 'manufacturing/job_confirm_delete.html', {'job': job})


# ---------------------------------------------------------------------------
# Material Requirements
# ---------------------------------------------------------------------------

@login_required
@supervisor_or_above
def requirement_add(request, pk):
    """Add a material requirement to a production job."""
    job = get_object_or_404(ProductionJob, pk=pk)

    if request.method == 'POST':
        form = MaterialRequirementForm(request.POST)
        if form.is_valid():
            req = form.save(commit=False)
            req.production_job = job
            req.created_by = request.user
            req.save()
            messages.success(request, f'Requirement added: {req.material.name}.')
        else:
            messages.error(request, 'Invalid data. Please check the form fields.')
    return redirect('manufacturing:job_detail', pk=job.pk)


@login_required
@supervisor_or_above
def requirement_delete(request, req_pk):
    """Remove a material requirement."""
    req = get_object_or_404(MaterialRequirement, pk=req_pk)
    job_pk = req.production_job_id
    req.delete()
    messages.success(request, 'Material requirement removed.')
    return redirect('manufacturing:job_detail', pk=job_pk)


# ---------------------------------------------------------------------------
# Update Stage Record
# ---------------------------------------------------------------------------

@login_required
def update_stage(request, pk):
    """Show and process the stage update form.

    GET  – render update_stage.html with the current record pre-filled.
    POST – process the update or advance action.
    Production workers may only update stages assigned to them.
    Supervisors and above may update any stage.
    """
    job = get_object_or_404(
        ProductionJob.objects.select_related('current_stage'),
        pk=pk,
    )

    # Permission check
    is_supervisor = _is_supervisor_or_above(request.user)
    current_record = _get_or_create_process_record(job, job.current_stage)

    if not is_supervisor:
        if current_record.assigned_to != request.user:
            return HttpResponseForbidden(
                '<h1>403 Forbidden</h1>'
                '<p>You are not assigned to this stage.</p>'
            )

    if request.method == 'GET':
        form = ProcessRecordForm(instance=current_record)
        return render(request, 'manufacturing/update_stage.html', {
            'form': form,
            'job': job,
            'current_record': current_record,
        })

    # POST handling
    action = request.POST.get('action', 'update')

    if action == 'advance':
        confirmed = request.POST.get('confirm') in ('true', 'on', '1')
        if confirmed:
            with transaction.atomic():
                if current_record.status not in ('COMPLETED', 'SKIPPED'):
                    current_record.status = 'COMPLETED'
                    current_record.completed_at = timezone.now()
                    current_record.save(update_fields=['status', 'completed_at'])

                next_stage = job.advance_to_next_stage()
                if next_stage is None:
                    job.status = STATUS_COMPLETED
                    job.actual_completion_date = timezone.now().date()
                    job.save(update_fields=['status', 'actual_completion_date', 'updated_at'])
                    messages.success(
                        request,
                        f'Job {job.job_number} has completed all stages and is now marked COMPLETED.',
                    )
                else:
                    _get_or_create_process_record(job, next_stage)
                    messages.success(
                        request,
                        f'Job {job.job_number} advanced to stage: {next_stage.name}.',
                    )
        else:
            messages.error(request, 'Advance action requires confirmation.')

    else:  # action == 'update'
        record_form = ProcessRecordForm(request.POST, instance=current_record)
        if record_form.is_valid():
            record = record_form.save(commit=False)
            if record.status == RECORD_STATUS_IN_PROGRESS and not record.started_at:
                record.started_at = timezone.now()
            if record.status == 'COMPLETED' and not record.completed_at:
                record.completed_at = timezone.now()
            record.save()
            messages.success(request, f'Stage record for "{job.current_stage.name}" updated.')
        else:
            messages.error(request, 'Please correct the errors in the update form.')

    return redirect('manufacturing:job_detail', pk=job.pk)


# ---------------------------------------------------------------------------
# Issue Materials
# ---------------------------------------------------------------------------

@login_required
@supervisor_or_above
def issue_materials(request, pk):
    """Issue raw materials for a production job. Supervisor and above only."""
    job = get_object_or_404(ProductionJob, pk=pk)

    if request.method == 'POST':
        form = MaterialIssuanceForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                issuance = form.save(commit=False)
                issuance.production_job = job
                issuance.issued_by = request.user
                issuance.save()

                # Deduct from inventory stock
                from inventory.models import CurrentStock, StockTransaction, TRANSACTION_OUT
                stock, _ = CurrentStock.objects.get_or_create(
                    material=issuance.material,
                    defaults={'quantity_on_hand': 0},
                )
                stock.quantity_on_hand -= issuance.quantity_issued
                stock.save()

                StockTransaction.objects.create(
                    material=issuance.material,
                    transaction_type=TRANSACTION_OUT,
                    quantity=issuance.quantity_issued,
                    reference_number=job.job_number,
                    notes=f'Issued for {job.job_number} — {issuance.stage.name}',
                    created_by=request.user,
                )

            messages.success(
                request,
                f'Issued {issuance.quantity_issued} {issuance.material.unit_of_measure} '
                f'of {issuance.material.name} for job {job.job_number}. Stock updated.',
            )
            return redirect('manufacturing:job_detail', pk=job.pk)
    else:
        # Pre-select current stage
        initial = {'stage': job.current_stage}
        form = MaterialIssuanceForm(initial=initial)

    context = {
        'form': form,
        'job': job,
    }
    return render(request, 'manufacturing/issue_materials.html', context)


# ---------------------------------------------------------------------------
# Quality Check Create
# ---------------------------------------------------------------------------

@login_required
def quality_check_create(request, record_pk):
    """Add a QC record linked to a process record."""
    process_record = get_object_or_404(
        ProcessRecord.objects.select_related(
            'production_job', 'stage'
        ),
        pk=record_pk,
    )
    job = process_record.production_job

    if request.method == 'POST':
        form = QualityCheckForm(request.POST)
        if form.is_valid():
            qc = form.save(commit=False)
            qc.process_record = process_record
            qc.checked_by = request.user
            qc.save()
            messages.success(
                request,
                f'Quality check recorded for {job.job_number} – {process_record.stage.name}.',
            )
            return redirect('manufacturing:job_detail', pk=job.pk)
    else:
        form = QualityCheckForm()

    context = {
        'form': form,
        'process_record': process_record,
        'job': job,
    }
    return render(request, 'manufacturing/quality_check_form.html', context)


# ---------------------------------------------------------------------------
# Final Product
# ---------------------------------------------------------------------------

@login_required
@supervisor_or_above
def final_product_create(request, pk):
    """Record or update the final product details and photo for a job."""
    job = get_object_or_404(ProductionJob, pk=pk)

    # Use existing record if it exists (edit in place)
    instance = getattr(job, 'final_product', None)

    if request.method == 'POST':
        form = FinalProductForm(request.POST, request.FILES, instance=instance)
        if form.is_valid():
            fp = form.save(commit=False)
            fp.production_job = job
            fp.created_by = request.user
            fp.save()
            messages.success(request, f'Final product recorded for {job.job_number}.')
            return redirect('manufacturing:job_detail', pk=job.pk)
    else:
        form = FinalProductForm(instance=instance)

    return render(request, 'manufacturing/final_product_form.html', {
        'form': form,
        'job': job,
        'existing': instance,
    })


# ---------------------------------------------------------------------------
# Final Product Inventory (data-entry list)
# ---------------------------------------------------------------------------

@login_required
def final_product_inventory(request):
    """List all final products; data-entry team can edit, supervisors+ can add."""
    from django.core.paginator import Paginator

    qs = (
        FinalProduct.objects
        .select_related('production_job', 'created_by')
        .order_by('-created_at')
    )

    # Filters
    search = request.GET.get('q', '').strip()
    metal  = request.GET.get('metal', '').strip()
    finish = request.GET.get('finish', '').strip()

    if search:
        qs = qs.filter(name__icontains=search) | qs.filter(
            production_job__job_number__icontains=search) | qs.filter(
            job_ref__icontains=search)
    if metal:
        qs = qs.filter(metal_type__icontains=metal)
    if finish:
        qs = qs.filter(finish=finish)

    paginator = Paginator(qs, 20)
    page = paginator.get_page(request.GET.get('page'))

    from .models import PRODUCT_FINISH_CHOICES
    return render(request, 'manufacturing/final_product_inventory.html', {
        'page_obj': page,
        'products': page.object_list,
        'finish_choices': PRODUCT_FINISH_CHOICES,
        'filter_search': search,
        'filter_metal': metal,
        'filter_finish': finish,
        'total': qs.count(),
        'can_manage': _is_supervisor_or_above(request.user),
    })


# ---------------------------------------------------------------------------
# Catalog — standalone add / edit / bulk upload
# ---------------------------------------------------------------------------

@login_required
def catalog_add(request):
    """Add a new catalog entry without linking to a production job."""
    if request.method == 'POST':
        form = FinalProductForm(request.POST, request.FILES)
        if form.is_valid():
            fp = form.save(commit=False)
            fp.created_by = request.user
            fp.save()
            messages.success(request, f'"{fp.name}" added to the catalog.')
            return redirect('manufacturing:final_product_inventory')
    else:
        form = FinalProductForm()

    return render(request, 'manufacturing/catalog_form.html', {
        'form': form,
        'title': 'Add Catalog Entry',
        'submit_label': 'Add to Catalog',
    })


@login_required
@supervisor_or_above
def catalog_edit(request, pk):
    """Edit an existing catalog entry."""
    product = get_object_or_404(FinalProduct, pk=pk)

    if request.method == 'POST':
        form = FinalProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, f'"{product.name}" updated.')
            return redirect('manufacturing:final_product_inventory')
    else:
        form = FinalProductForm(instance=product)

    return render(request, 'manufacturing/catalog_form.html', {
        'form': form,
        'product': product,
        'title': f'Edit — {product.name}',
        'submit_label': 'Save Changes',
    })


@login_required
def catalog_bulk_upload(request):
    """Upload a CSV file to bulk-create catalog entries."""
    import csv
    import io
    from .models import PRODUCT_FINISH_CHOICES

    VALID_FINISHES = {v for v, _ in PRODUCT_FINISH_CHOICES}
    results = []

    if request.method == 'POST':
        form = CatalogBulkUploadForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = request.FILES['csv_file']
            decoded = csv_file.read().decode('utf-8-sig')
            reader = csv.DictReader(io.StringIO(decoded))

            created = 0
            errors = []
            for row_num, row in enumerate(reader, start=2):
                name = row.get('name', '').strip()
                if not name:
                    errors.append(f'Row {row_num}: "name" is required — skipped.')
                    continue
                finish = row.get('finish', '').strip().upper()
                if finish and finish not in VALID_FINISHES:
                    finish = 'POLISHED'

                try:
                    weight_raw = row.get('final_weight', '').strip()
                    weight = float(weight_raw) if weight_raw else None
                except ValueError:
                    weight = None

                FinalProduct.objects.create(
                    name=name,
                    job_ref=row.get('job_ref', '').strip(),
                    metal_type=row.get('metal_type', '').strip(),
                    purity=row.get('purity', '').strip(),
                    final_weight=weight,
                    finish=finish or 'POLISHED',
                    stone_details=row.get('stone_details', '').strip(),
                    hallmark=row.get('hallmark', '').strip(),
                    description=row.get('description', '').strip(),
                    notes=row.get('notes', '').strip(),
                    created_by=request.user,
                )
                created += 1

            if created:
                messages.success(request, f'{created} product{"s" if created != 1 else ""} imported successfully.')
            for err in errors:
                messages.warning(request, err)
            if created:
                return redirect('manufacturing:final_product_inventory')
    else:
        form = CatalogBulkUploadForm()

    return render(request, 'manufacturing/catalog_bulk_upload.html', {'form': form})
