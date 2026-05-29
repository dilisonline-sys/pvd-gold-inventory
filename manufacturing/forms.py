from django import forms
from django.contrib.auth import get_user_model

from .models import (
    FinalProduct,
    MaterialIssuance,
    MaterialRequirement,
    ProcessRecord,
    ProcessStage,
    ProductionJob,
    QualityCheck,
)

User = get_user_model()


class ProductionJobForm(forms.ModelForm):
    """Create or edit a ProductionJob."""

    class Meta:
        model = ProductionJob
        fields = [
            'job_order',
            'title',
            'description',
            'current_stage',
            'status',
            'priority',
            'target_completion_date',
        ]
        widgets = {
            'target_completion_date': forms.DateInput(
                attrs={'type': 'date', 'class': 'form-control'},
            ),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'job_order': forms.Select(attrs={'class': 'form-select'}),
            'current_stage': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['job_order'].required = False
        self.fields['current_stage'].queryset = ProcessStage.objects.filter(
            is_active=True
        ).order_by('order_number')


class ProcessRecordForm(forms.ModelForm):
    """Update notes, weights, status and assignment for a stage record."""

    class Meta:
        model = ProcessRecord
        fields = [
            'assigned_to',
            'status',
            'started_at',
            'completed_at',
            'notes',
            'weight_in',
            'weight_out',
            'waste_weight',
            'remarks',
        ]
        widgets = {
            'assigned_to': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'started_at': forms.DateTimeInput(
                attrs={'class': 'form-control', 'type': 'datetime-local'},
                format='%Y-%m-%dT%H:%M',
            ),
            'completed_at': forms.DateTimeInput(
                attrs={'class': 'form-control', 'type': 'datetime-local'},
                format='%Y-%m-%dT%H:%M',
            ),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'weight_in': forms.NumberInput(
                attrs={'class': 'form-control', 'step': '0.0001'}
            ),
            'weight_out': forms.NumberInput(
                attrs={'class': 'form-control', 'step': '0.0001'}
            ),
            'waste_weight': forms.NumberInput(
                attrs={'class': 'form-control', 'step': '0.0001'}
            ),
            'remarks': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['assigned_to'].required = False
        self.fields['assigned_to'].queryset = User.objects.filter(
            is_active=True
        ).order_by('username')
        self.fields['started_at'].required = False
        self.fields['completed_at'].required = False


class MaterialIssuanceForm(forms.ModelForm):
    """Issue raw materials for a production job at a given stage."""

    class Meta:
        model = MaterialIssuance
        fields = [
            'material',
            'stage',
            'quantity_requested',
            'quantity_issued',
            'notes',
        ]
        widgets = {
            'material': forms.Select(attrs={'class': 'form-select'}),
            'stage': forms.Select(attrs={'class': 'form-select'}),
            'quantity_requested': forms.NumberInput(
                attrs={'class': 'form-control', 'step': '0.0001'}
            ),
            'quantity_issued': forms.NumberInput(
                attrs={'class': 'form-control', 'step': '0.0001'}
            ),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['stage'].queryset = ProcessStage.objects.filter(
            is_active=True
        ).order_by('order_number')


class QualityCheckForm(forms.ModelForm):
    """Add a quality control record for a process record."""

    class Meta:
        model = QualityCheck
        fields = [
            'result',
            'weight',
            'dimensions',
            'finish_grade',
            'defects_found',
            'corrective_action',
            'approved_by',
        ]
        widgets = {
            'result': forms.Select(attrs={'class': 'form-select'}),
            'weight': forms.NumberInput(
                attrs={'class': 'form-control', 'step': '0.0001'}
            ),
            'dimensions': forms.TextInput(attrs={'class': 'form-control'}),
            'finish_grade': forms.Select(attrs={'class': 'form-select'}),
            'defects_found': forms.Textarea(
                attrs={'class': 'form-control', 'rows': 3}
            ),
            'corrective_action': forms.Textarea(
                attrs={'class': 'form-control', 'rows': 3}
            ),
            'approved_by': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['approved_by'].required = False
        self.fields['weight'].required = False
        self.fields['approved_by'].queryset = User.objects.filter(
            is_active=True
        ).order_by('username')


class StageAdvanceForm(forms.Form):
    """Simple confirmation form used when advancing a job to the next stage."""

    confirmation_notes = forms.CharField(
        label='Notes / Reason for Advancement',
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        required=False,
        help_text='Optional notes explaining why the job is advancing to the next stage.',
    )
    confirm = forms.BooleanField(
        label='I confirm that this stage is complete and ready to advance.',
        required=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
    )


class FinalProductForm(forms.ModelForm):
    """Record the finished product details and photo for a catalog entry."""

    class Meta:
        model = FinalProduct
        fields = [
            'name', 'job_ref', 'description', 'metal_type', 'purity',
            'final_weight', 'finish', 'stone_details', 'hallmark',
            'image', 'notes',
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'job_ref': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. JOB-2025-001'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'metal_type': forms.TextInput(attrs={'class': 'form-control'}),
            'purity': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 18K, 22K, 925'}),
            'final_weight': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.0001'}),
            'finish': forms.Select(attrs={'class': 'form-select'}),
            'stone_details': forms.Textarea(attrs={'class': 'form-control', 'rows': 2,
                                                   'placeholder': 'e.g. 1ct round diamond centre, 8 baguette accents'}),
            'hallmark': forms.TextInput(attrs={'class': 'form-control',
                                               'placeholder': 'e.g. 750, 916, PVD stamp'}),
            'image': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class MaterialRequirementForm(forms.ModelForm):
    """Add a material requirement to a production job."""

    class Meta:
        model = MaterialRequirement
        fields = ['material', 'quantity_required', 'notes']
        widgets = {
            'material': forms.Select(attrs={'class': 'form-select'}),
            'quantity_required': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.0001'}),
            'notes': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Optional note'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from inventory.models import RawMaterial
        self.fields['material'].queryset = (
            RawMaterial.objects.filter(is_active=True)
            .select_related('category')
            .order_by('category__name', 'name')
        )
        self.fields['notes'].required = False


class CatalogBulkUploadForm(forms.Form):
    """Upload a CSV file to bulk-create catalog entries."""
    csv_file = forms.FileField(
        label='CSV File',
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': '.csv'}),
        help_text='Required columns: name. Optional: job_ref, metal_type, purity, final_weight, finish, stone_details, hallmark, description, notes',
    )
