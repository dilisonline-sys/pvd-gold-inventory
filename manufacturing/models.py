from django.conf import settings
from django.db import models
from django.utils import timezone


# ---------------------------------------------------------------------------
# Choices
# ---------------------------------------------------------------------------

STATUS_PENDING = 'PENDING'
STATUS_IN_PROGRESS = 'IN_PROGRESS'
STATUS_ON_HOLD = 'ON_HOLD'
STATUS_COMPLETED = 'COMPLETED'
STATUS_CANCELLED = 'CANCELLED'

JOB_STATUS_CHOICES = [
    (STATUS_PENDING, 'Pending'),
    (STATUS_IN_PROGRESS, 'In Progress'),
    (STATUS_ON_HOLD, 'On Hold'),
    (STATUS_COMPLETED, 'Completed'),
    (STATUS_CANCELLED, 'Cancelled'),
]

PRIORITY_LOW = 'LOW'
PRIORITY_MEDIUM = 'MEDIUM'
PRIORITY_HIGH = 'HIGH'
PRIORITY_URGENT = 'URGENT'

PRIORITY_CHOICES = [
    (PRIORITY_LOW, 'Low'),
    (PRIORITY_MEDIUM, 'Medium'),
    (PRIORITY_HIGH, 'High'),
    (PRIORITY_URGENT, 'Urgent'),
]

RECORD_STATUS_PENDING = 'PENDING'
RECORD_STATUS_IN_PROGRESS = 'IN_PROGRESS'
RECORD_STATUS_COMPLETED = 'COMPLETED'
RECORD_STATUS_FAILED = 'FAILED'
RECORD_STATUS_SKIPPED = 'SKIPPED'

RECORD_STATUS_CHOICES = [
    (RECORD_STATUS_PENDING, 'Pending'),
    (RECORD_STATUS_IN_PROGRESS, 'In Progress'),
    (RECORD_STATUS_COMPLETED, 'Completed'),
    (RECORD_STATUS_FAILED, 'Failed'),
    (RECORD_STATUS_SKIPPED, 'Skipped'),
]

QC_RESULT_PASS = 'PASS'
QC_RESULT_FAIL = 'FAIL'
QC_RESULT_CONDITIONAL = 'CONDITIONAL'

QC_RESULT_CHOICES = [
    (QC_RESULT_PASS, 'Pass'),
    (QC_RESULT_FAIL, 'Fail'),
    (QC_RESULT_CONDITIONAL, 'Conditional'),
]

FINISH_GRADE_A = 'A'
FINISH_GRADE_B = 'B'
FINISH_GRADE_C = 'C'
FINISH_GRADE_REJECT = 'REJECT'

FINISH_GRADE_CHOICES = [
    (FINISH_GRADE_A, 'Grade A'),
    (FINISH_GRADE_B, 'Grade B'),
    (FINISH_GRADE_C, 'Grade C'),
    (FINISH_GRADE_REJECT, 'Reject'),
]


# ---------------------------------------------------------------------------
# ProcessStage
# ---------------------------------------------------------------------------

class ProcessStage(models.Model):
    """Defines a single stage in the jewelry manufacturing workflow."""

    DESIGN = 'DESIGN'
    WAX_CARVING = 'WAX_CARVING'
    INVESTMENT = 'INVESTMENT'
    CASTING = 'CASTING'
    FILING = 'FILING'
    POLISHING = 'POLISHING'
    STONE_SETTING = 'STONE_SETTING'
    QUALITY_CHECK = 'QUALITY_CHECK'
    PLATING = 'PLATING'
    FINAL_INSPECTION = 'FINAL_INSPECTION'
    PACKAGING = 'PACKAGING'

    STAGE_CODE_CHOICES = [
        (DESIGN, 'Design & Specification'),
        (WAX_CARVING, 'Wax Carving / CAD Modeling'),
        (INVESTMENT, 'Investment & Burnout'),
        (CASTING, 'Metal Casting'),
        (FILING, 'Filing & Sprue Removal'),
        (POLISHING, 'Polishing & Cleaning'),
        (STONE_SETTING, 'Stone Setting'),
        (QUALITY_CHECK, 'Quality Control Check'),
        (PLATING, 'Plating & Finishing'),
        (FINAL_INSPECTION, 'Final Inspection'),
        (PACKAGING, 'Packaging & Delivery Ready'),
    ]

    name = models.CharField(max_length=150, verbose_name='Stage Name')
    code = models.CharField(
        max_length=50,
        unique=True,
        choices=STAGE_CODE_CHOICES,
        verbose_name='Stage Code',
    )
    order_number = models.PositiveIntegerField(
        unique=True,
        verbose_name='Order Number',
        help_text='Defines the sequence of stages in the manufacturing workflow.',
    )
    description = models.TextField(blank=True, verbose_name='Description')
    is_active = models.BooleanField(default=True, verbose_name='Active')

    class Meta:
        verbose_name = 'Process Stage'
        verbose_name_plural = 'Process Stages'
        ordering = ['order_number']

    def __str__(self):
        return f'{self.order_number}. {self.name}'

    def get_next_stage(self):
        """Return the next ProcessStage by order_number, or None if this is the last."""
        return (
            ProcessStage.objects
            .filter(order_number__gt=self.order_number, is_active=True)
            .order_by('order_number')
            .first()
        )


# ---------------------------------------------------------------------------
# ProductionJob
# ---------------------------------------------------------------------------

class ProductionJob(models.Model):
    """Represents a single jewelry item moving through the manufacturing pipeline."""

    job_order = models.ForeignKey(
        'orders.JobOrder',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='production_jobs',
        verbose_name='Job Order',
    )
    job_number = models.CharField(
        max_length=20,
        unique=True,
        editable=False,
        verbose_name='Job Number',
        help_text='Auto-generated in format PJ-YYYY-NNNN.',
    )
    title = models.CharField(max_length=200, verbose_name='Title')
    description = models.TextField(blank=True, verbose_name='Description')
    current_stage = models.ForeignKey(
        ProcessStage,
        on_delete=models.PROTECT,
        related_name='current_jobs',
        verbose_name='Current Stage',
    )
    status = models.CharField(
        max_length=20,
        choices=JOB_STATUS_CHOICES,
        default=STATUS_PENDING,
        verbose_name='Status',
    )
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default=PRIORITY_MEDIUM,
        verbose_name='Priority',
    )
    target_completion_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='Target Completion Date',
    )
    actual_completion_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='Actual Completion Date',
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='production_jobs_created',
        verbose_name='Created By',
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Created At')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Updated At')

    class Meta:
        verbose_name = 'Production Job'
        verbose_name_plural = 'Production Jobs'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.job_number} – {self.title}'

    # ------------------------------------------------------------------
    # Job number generation
    # ------------------------------------------------------------------

    def _generate_job_number(self):
        year = timezone.now().year
        prefix = f'PJ-{year}-'
        last = (
            ProductionJob.objects
            .filter(job_number__startswith=prefix)
            .order_by('job_number')
            .last()
        )
        if last:
            try:
                seq = int(last.job_number.split('-')[-1]) + 1
            except (ValueError, IndexError):
                seq = 1
        else:
            seq = 1
        return f'{prefix}{seq:04d}'

    def save(self, *args, **kwargs):
        if not self.job_number:
            self.job_number = self._generate_job_number()
        super().save(*args, **kwargs)

    # ------------------------------------------------------------------
    # Stage advancement
    # ------------------------------------------------------------------

    def advance_to_next_stage(self):
        """
        Move this job to the next ProcessStage (by order_number).

        Returns the new stage if advanced, or None if already at the last stage.
        Marks the job status as IN_PROGRESS when advancing.
        """
        next_stage = self.current_stage.get_next_stage()
        if next_stage is None:
            return None
        self.current_stage = next_stage
        if self.status == STATUS_PENDING:
            self.status = STATUS_IN_PROGRESS
        self.save(update_fields=['current_stage', 'status', 'updated_at'])
        return next_stage


# ---------------------------------------------------------------------------
# ProcessRecord
# ---------------------------------------------------------------------------

class ProcessRecord(models.Model):
    """Tracks the work performed at a specific stage for a specific production job."""

    production_job = models.ForeignKey(
        ProductionJob,
        on_delete=models.CASCADE,
        related_name='process_records',
        verbose_name='Production Job',
    )
    stage = models.ForeignKey(
        ProcessStage,
        on_delete=models.PROTECT,
        related_name='process_records',
        verbose_name='Stage',
    )
    started_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Started At',
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Completed At',
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='process_records',
        verbose_name='Assigned To',
    )
    notes = models.TextField(blank=True, verbose_name='Notes')
    status = models.CharField(
        max_length=20,
        choices=RECORD_STATUS_CHOICES,
        default=RECORD_STATUS_PENDING,
        verbose_name='Status',
    )
    weight_in = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        null=True,
        blank=True,
        verbose_name='Weight In (g)',
        help_text='Weight of piece entering this stage, in grams.',
    )
    weight_out = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        null=True,
        blank=True,
        verbose_name='Weight Out (g)',
        help_text='Weight of piece leaving this stage, in grams.',
    )
    waste_weight = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        null=True,
        blank=True,
        verbose_name='Waste Weight (g)',
        help_text='Measured waste/scrap generated at this stage, in grams.',
    )
    remarks = models.TextField(blank=True, verbose_name='Remarks')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Created At')

    class Meta:
        verbose_name = 'Process Record'
        verbose_name_plural = 'Process Records'
        ordering = ['-created_at']
        unique_together = [('production_job', 'stage')]

    def save(self, *args, **kwargs):
        if self.status == RECORD_STATUS_IN_PROGRESS and not self.started_at:
            self.started_at = timezone.now()
        if self.status == RECORD_STATUS_COMPLETED and not self.completed_at:
            self.completed_at = timezone.now()
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.production_job.job_number} – {self.stage.name}'

    @property
    def weight_loss(self):
        """Return weight lost during this stage (weight_in minus weight_out)."""
        if self.weight_in is not None and self.weight_out is not None:
            return self.weight_in - self.weight_out
        return None


# ---------------------------------------------------------------------------
# MaterialIssuance
# ---------------------------------------------------------------------------

class MaterialIssuance(models.Model):
    """Records materials issued from inventory for a production job at a given stage."""

    production_job = models.ForeignKey(
        ProductionJob,
        on_delete=models.CASCADE,
        related_name='material_issuances',
        verbose_name='Production Job',
    )
    material = models.ForeignKey(
        'inventory.RawMaterial',
        on_delete=models.PROTECT,
        related_name='material_issuances',
        verbose_name='Material',
    )
    quantity_requested = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        verbose_name='Quantity Requested',
    )
    quantity_issued = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        verbose_name='Quantity Issued',
    )
    issued_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='material_issuances',
        verbose_name='Issued By',
    )
    issued_at = models.DateTimeField(
        default=timezone.now,
        verbose_name='Issued At',
    )
    stage = models.ForeignKey(
        ProcessStage,
        on_delete=models.PROTECT,
        related_name='material_issuances',
        verbose_name='Stage',
    )
    notes = models.TextField(blank=True, verbose_name='Notes')

    class Meta:
        verbose_name = 'Material Issuance'
        verbose_name_plural = 'Material Issuances'
        ordering = ['-issued_at']

    def __str__(self):
        return (
            f'{self.material.name} x {self.quantity_issued} '
            f'→ {self.production_job.job_number} ({self.stage.name})'
        )


# ---------------------------------------------------------------------------
# MaterialRequirement
# ---------------------------------------------------------------------------

class MaterialRequirement(models.Model):
    """Planned material needed for a production job before issuance."""

    production_job = models.ForeignKey(
        ProductionJob,
        on_delete=models.CASCADE,
        related_name='material_requirements',
        verbose_name='Production Job',
    )
    material = models.ForeignKey(
        'inventory.RawMaterial',
        on_delete=models.PROTECT,
        related_name='material_requirements',
        verbose_name='Material',
    )
    quantity_required = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        verbose_name='Quantity Required',
    )
    notes = models.CharField(max_length=200, blank=True, verbose_name='Notes')
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='material_requirements_created',
        verbose_name='Added By',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Material Requirement'
        verbose_name_plural = 'Material Requirements'
        ordering = ['material__category__name', 'material__name']

    def __str__(self):
        return f'{self.production_job.job_number} needs {self.quantity_required} × {self.material.name}'

    @property
    def current_stock(self):
        return self.material.get_current_stock()

    @property
    def is_available(self):
        return self.current_stock >= self.quantity_required

    @property
    def shortfall(self):
        diff = self.current_stock - self.quantity_required
        return abs(diff) if diff < 0 else 0


# ---------------------------------------------------------------------------
# QualityCheck
# ---------------------------------------------------------------------------

class QualityCheck(models.Model):
    """Quality control record associated with a process record."""

    process_record = models.ForeignKey(
        ProcessRecord,
        on_delete=models.CASCADE,
        related_name='quality_checks',
        verbose_name='Process Record',
    )
    checked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='quality_checks_performed',
        verbose_name='Checked By',
    )
    checked_at = models.DateTimeField(
        default=timezone.now,
        verbose_name='Checked At',
    )
    result = models.CharField(
        max_length=20,
        choices=QC_RESULT_CHOICES,
        verbose_name='Result',
    )
    weight = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        null=True,
        blank=True,
        verbose_name='Weight (g)',
    )
    dimensions = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Dimensions',
        help_text='e.g. 25mm x 15mm x 3mm',
    )
    finish_grade = models.CharField(
        max_length=10,
        choices=FINISH_GRADE_CHOICES,
        verbose_name='Finish Grade',
    )
    defects_found = models.TextField(
        blank=True,
        verbose_name='Defects Found',
    )
    corrective_action = models.TextField(
        blank=True,
        verbose_name='Corrective Action',
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='quality_checks_approved',
        verbose_name='Approved By',
    )

    class Meta:
        verbose_name = 'Quality Check'
        verbose_name_plural = 'Quality Checks'
        ordering = ['-checked_at']

    def __str__(self):
        return (
            f'QC {self.process_record} – {self.get_result_display()} '
            f'({self.checked_at:%Y-%m-%d})'
        )


# ---------------------------------------------------------------------------
# FinalProduct
# ---------------------------------------------------------------------------

FINISH_POLISHED = 'POLISHED'
FINISH_MATTE = 'MATTE'
FINISH_BRUSHED = 'BRUSHED'
FINISH_HAMMERED = 'HAMMERED'
FINISH_SANDBLAST = 'SANDBLAST'
FINISH_OTHER = 'OTHER'

PRODUCT_FINISH_CHOICES = [
    (FINISH_POLISHED, 'High Polish'),
    (FINISH_MATTE, 'Matte'),
    (FINISH_BRUSHED, 'Brushed'),
    (FINISH_HAMMERED, 'Hammered'),
    (FINISH_SANDBLAST, 'Sandblast'),
    (FINISH_OTHER, 'Other'),
]


class FinalProduct(models.Model):
    """Catalog entry for a finished product — may be linked to a production job or standalone."""

    production_job = models.OneToOneField(
        ProductionJob,
        on_delete=models.CASCADE,
        related_name='final_product',
        verbose_name='Production Job',
        null=True,
        blank=True,
    )
    job_ref = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='Job Reference',
        help_text='Manual job/order reference when not linked to a production job.',
    )
    name = models.CharField(max_length=200, verbose_name='Product Name')
    description = models.TextField(blank=True, verbose_name='Description')
    metal_type = models.CharField(max_length=100, blank=True, verbose_name='Metal Type')
    purity = models.CharField(max_length=20, blank=True, verbose_name='Purity / Karat')
    final_weight = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        null=True,
        blank=True,
        verbose_name='Final Weight (g)',
    )
    finish = models.CharField(
        max_length=20,
        choices=PRODUCT_FINISH_CHOICES,
        default=FINISH_POLISHED,
        verbose_name='Surface Finish',
    )
    stone_details = models.TextField(blank=True, verbose_name='Stone / Gem Details')
    hallmark = models.CharField(max_length=100, blank=True, verbose_name='Hallmark / Stamp')
    image = models.ImageField(
        upload_to='final_products/',
        null=True,
        blank=True,
        verbose_name='Product Photo',
    )
    notes = models.TextField(blank=True, verbose_name='Additional Notes')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Recorded At')
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='final_products_recorded',
        verbose_name='Recorded By',
    )

    class Meta:
        verbose_name = 'Final Product'
        verbose_name_plural = 'Final Products'
        ordering = ['-created_at']

    def __str__(self):
        ref = self.production_job.job_number if self.production_job_id else (self.job_ref or '—')
        return f'{ref} – {self.name}'

    @property
    def display_job_ref(self):
        if self.production_job_id:
            return self.production_job.job_number
        return self.job_ref or '—'
