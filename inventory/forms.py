import csv
import io

from django import forms
from django.core.exceptions import ValidationError

from .models import MaterialCategory, RawMaterial, StockEntry, StockTransaction, Supplier


# ---------------------------------------------------------------------------
# MaterialForm
# ---------------------------------------------------------------------------

class MaterialForm(forms.ModelForm):
    class Meta:
        model = RawMaterial
        fields = [
            'name',
            'category',
            'unit_of_measure',
            'description',
            'minimum_stock_level',
            'is_active',
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'unit_of_measure': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'minimum_stock_level': forms.NumberInput(
                attrs={'class': 'form-control', 'step': '0.0001', 'min': '0'}
            ),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


# ---------------------------------------------------------------------------
# SupplierForm
# ---------------------------------------------------------------------------

class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = ['name', 'contact_person', 'phone', 'email', 'address', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'contact_person': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


# ---------------------------------------------------------------------------
# StockEntryForm
# ---------------------------------------------------------------------------

class StockEntryForm(forms.ModelForm):
    class Meta:
        model = StockEntry
        fields = [
            'material',
            'supplier',
            'quantity',
            'unit_cost',
            'entry_date',
            'batch_number',
            'purity',
            'notes',
        ]
        widgets = {
            'material': forms.Select(attrs={'class': 'form-select'}),
            'supplier': forms.Select(attrs={'class': 'form-select'}),
            'quantity': forms.NumberInput(
                attrs={'class': 'form-control', 'step': '0.0001', 'min': '0.0001'}
            ),
            'unit_cost': forms.NumberInput(
                attrs={'class': 'form-control', 'step': '0.0001', 'min': '0'}
            ),
            'entry_date': forms.DateInput(
                attrs={'class': 'form-control', 'type': 'date'}
            ),
            'batch_number': forms.TextInput(attrs={'class': 'form-control'}),
            'purity': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': 'e.g. 18k, 22k, 24k, 999'}
            ),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['material'].queryset = (
            RawMaterial.objects.filter(is_active=True).select_related('category')
        )
        self.fields['supplier'].queryset = Supplier.objects.filter(is_active=True)
        self.fields['supplier'].required = False

    def clean_quantity(self):
        qty = self.cleaned_data.get('quantity')
        if qty is not None and qty <= 0:
            raise ValidationError('Quantity must be greater than zero.')
        return qty

    def clean_unit_cost(self):
        cost = self.cleaned_data.get('unit_cost')
        if cost is not None and cost < 0:
            raise ValidationError('Unit cost cannot be negative.')
        return cost


# ---------------------------------------------------------------------------
# BulkStockEntryForm
# ---------------------------------------------------------------------------

REQUIRED_CSV_COLUMNS = {
    'material_name',
    'quantity',
    'unit_cost',
}

OPTIONAL_CSV_COLUMNS = {
    'supplier_name',
    'batch_number',
    'purity',
    'notes',
}

ALL_CSV_COLUMNS = REQUIRED_CSV_COLUMNS | OPTIONAL_CSV_COLUMNS


class BulkStockEntryForm(forms.Form):
    """Upload a CSV file to create multiple StockEntry records at once.

    Expected CSV columns (header row required):
        material_name, quantity, unit_cost, supplier_name, batch_number, purity, notes

    Only material_name, quantity and unit_cost are required per row.
    """

    csv_file = forms.FileField(
        label='CSV File',
        help_text=(
            'Required columns: material_name, quantity, unit_cost. '
            'Optional: supplier_name, batch_number, purity, notes.'
        ),
        widget=forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': '.csv'}),
    )
    material_category = forms.ModelChoiceField(
        queryset=MaterialCategory.objects.all(),
        required=False,
        empty_label='— All Categories —',
        label='Filter by Category',
        help_text='Only validate materials belonging to this category (optional).',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )

    def clean_csv_file(self):
        uploaded = self.cleaned_data['csv_file']

        if not uploaded.name.lower().endswith('.csv'):
            raise ValidationError('Only CSV files are accepted.')

        if uploaded.size > 5 * 1024 * 1024:  # 5 MB guard
            raise ValidationError('CSV file must not exceed 5 MB.')

        try:
            text = uploaded.read().decode('utf-8-sig')  # handle BOM
        except UnicodeDecodeError:
            raise ValidationError('Could not decode file. Please save as UTF-8 CSV.')

        reader = csv.DictReader(io.StringIO(text))
        if reader.fieldnames is None:
            raise ValidationError('The CSV file appears to be empty.')

        normalized_headers = {h.strip().lower() for h in reader.fieldnames}
        missing = REQUIRED_CSV_COLUMNS - normalized_headers
        if missing:
            raise ValidationError(
                f'Missing required CSV columns: {", ".join(sorted(missing))}.'
            )

        rows = []
        row_errors = []
        for i, row in enumerate(reader, start=2):
            cleaned_row = {k.strip().lower(): v.strip() for k, v in row.items() if k}

            if not cleaned_row.get('material_name'):
                row_errors.append(f'Row {i}: material_name is empty.')
                continue
            try:
                qty = float(cleaned_row.get('quantity', ''))
                if qty <= 0:
                    row_errors.append(f'Row {i}: quantity must be positive.')
                    continue
            except (ValueError, TypeError):
                row_errors.append(f'Row {i}: quantity is not a valid number.')
                continue
            try:
                cost = float(cleaned_row.get('unit_cost', ''))
                if cost < 0:
                    row_errors.append(f'Row {i}: unit_cost cannot be negative.')
                    continue
            except (ValueError, TypeError):
                row_errors.append(f'Row {i}: unit_cost is not a valid number.')
                continue

            rows.append(cleaned_row)

        if row_errors:
            raise ValidationError(row_errors)

        if not rows:
            raise ValidationError('The CSV file contains no data rows.')

        uploaded.seek(0)
        self._parsed_rows = rows
        return uploaded

    def get_parsed_rows(self):
        """Return the list of dicts parsed during validation."""
        return getattr(self, '_parsed_rows', [])


# ---------------------------------------------------------------------------
# StockAdjustmentForm
# ---------------------------------------------------------------------------

ADJUSTMENT_ADD = 'add'
ADJUSTMENT_SUBTRACT = 'subtract'
ADJUSTMENT_SET = 'set'

ADJUSTMENT_MODE_CHOICES = [
    (ADJUSTMENT_ADD, 'Add to current stock'),
    (ADJUSTMENT_SUBTRACT, 'Subtract from current stock'),
    (ADJUSTMENT_SET, 'Set stock to exact value'),
]


class StockAdjustmentForm(forms.Form):
    material = forms.ModelChoiceField(
        queryset=RawMaterial.objects.filter(is_active=True).select_related('category'),
        label='Material',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    adjustment_mode = forms.ChoiceField(
        choices=ADJUSTMENT_MODE_CHOICES,
        initial=ADJUSTMENT_ADD,
        label='Adjustment Mode',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    quantity = forms.DecimalField(
        max_digits=12,
        decimal_places=4,
        min_value=0,
        label='Quantity',
        widget=forms.NumberInput(
            attrs={'class': 'form-control', 'step': '0.0001', 'min': '0'}
        ),
    )
    reference_number = forms.CharField(
        max_length=100,
        required=False,
        label='Reference Number',
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )
    notes = forms.CharField(
        required=False,
        label='Notes',
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
    )

    def clean(self):
        cleaned = super().clean()
        mode = cleaned.get('adjustment_mode')
        qty = cleaned.get('quantity')
        material = cleaned.get('material')

        if mode == ADJUSTMENT_SUBTRACT and qty is not None and material is not None:
            current = material.get_current_stock()
            if qty > current:
                raise ValidationError(
                    f'Cannot subtract {qty} from current stock of {current}. '
                    'The result would be negative.'
                )
        return cleaned
