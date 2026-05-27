from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone

from .models import (
    Customer,
    ItemType,
    JobOrder,
    OrderNote,
    ORDER_STATUS_CHOICES,
    PRIORITY_CHOICES,
)


# ---------------------------------------------------------------------------
# CustomerForm
# ---------------------------------------------------------------------------

class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['name', 'phone', 'email', 'address', 'notes', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


# ---------------------------------------------------------------------------
# JobOrderForm
# ---------------------------------------------------------------------------

class JobOrderForm(forms.ModelForm):
    class Meta:
        model = JobOrder
        fields = [
            'customer',
            'item_type',
            'description',
            'quantity',
            'metal_type',
            'metal_purity',
            'estimated_weight',
            'stone_type',
            'stone_weight',
            'special_instructions',
            'status',
            'priority',
            'order_date',
            'required_date',
            'estimated_cost',
            'advance_payment',
        ]
        widgets = {
            'customer': forms.Select(attrs={'class': 'form-select'}),
            'item_type': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'metal_type': forms.Select(attrs={'class': 'form-select'}),
            'metal_purity': forms.Select(attrs={'class': 'form-select'}),
            'estimated_weight': forms.NumberInput(
                attrs={'class': 'form-control', 'step': '0.0001', 'min': '0.0001'}
            ),
            'stone_type': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': 'e.g. Diamond, Ruby'}
            ),
            'stone_weight': forms.NumberInput(
                attrs={'class': 'form-control', 'step': '0.0001', 'min': '0'}
            ),
            'special_instructions': forms.Textarea(
                attrs={'class': 'form-control', 'rows': 3}
            ),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'order_date': forms.DateInput(
                attrs={'class': 'form-control', 'type': 'date'}
            ),
            'required_date': forms.DateInput(
                attrs={'class': 'form-control', 'type': 'date'}
            ),
            'estimated_cost': forms.NumberInput(
                attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}
            ),
            'advance_payment': forms.NumberInput(
                attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['customer'].queryset = Customer.objects.filter(is_active=True)
        self.fields['stone_type'].required = False
        self.fields['stone_weight'].required = False

    def clean(self):
        cleaned = super().clean()
        order_date = cleaned.get('order_date')
        required_date = cleaned.get('required_date')
        if order_date and required_date and required_date < order_date:
            raise ValidationError(
                {'required_date': 'Required date cannot be earlier than order date.'}
            )
        advance = cleaned.get('advance_payment')
        estimated = cleaned.get('estimated_cost')
        if advance is not None and estimated is not None and advance > estimated:
            raise ValidationError(
                {'advance_payment': 'Advance payment cannot exceed the estimated cost.'}
            )
        return cleaned


# ---------------------------------------------------------------------------
# OrderNoteForm
# ---------------------------------------------------------------------------

class OrderNoteForm(forms.ModelForm):
    class Meta:
        model = OrderNote
        fields = ['note']
        widgets = {
            'note': forms.Textarea(
                attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Add a note…'}
            ),
        }


# ---------------------------------------------------------------------------
# OrderStatusUpdateForm
# ---------------------------------------------------------------------------

class OrderStatusUpdateForm(forms.Form):
    status = forms.ChoiceField(
        choices=ORDER_STATUS_CHOICES,
        label='New Status',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    note = forms.CharField(
        required=False,
        label='Note (optional)',
        widget=forms.Textarea(
            attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Reason for status change…',
            }
        ),
    )


# ---------------------------------------------------------------------------
# OrderDeliveryForm  (actual weight, cost, delivery date)
# ---------------------------------------------------------------------------

class OrderDeliveryForm(forms.ModelForm):
    class Meta:
        model = JobOrder
        fields = ['actual_weight', 'actual_cost', 'advance_payment', 'delivery_date']
        widgets = {
            'actual_weight': forms.NumberInput(
                attrs={'class': 'form-control', 'step': '0.0001', 'min': '0'}
            ),
            'actual_cost': forms.NumberInput(
                attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}
            ),
            'advance_payment': forms.NumberInput(
                attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}
            ),
            'delivery_date': forms.DateInput(
                attrs={'class': 'form-control', 'type': 'date'}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['actual_weight'].required = True
        self.fields['actual_cost'].required = True
        self.fields['delivery_date'].required = True
        if not self.initial.get('delivery_date'):
            self.initial['delivery_date'] = timezone.now().date()
