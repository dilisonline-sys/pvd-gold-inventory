from django import forms
from django.contrib.auth import get_user_model

from .models import (
    ProductionJob,
    ProcessRecord,
    MaterialIssuance,
    QualityCheck,
    ProcessStage,
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
            'notes',
            'weight_in',
            'weight_out',
            'waste_weight',
            'remarks',
        ]
        widgets = {
            'assigned_to': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
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
