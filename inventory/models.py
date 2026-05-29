from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils import timezone


# ---------------------------------------------------------------------------
# Choices
# ---------------------------------------------------------------------------

UNIT_GRAMS = 'grams'
UNIT_CARATS = 'carats'
UNIT_PIECES = 'pieces'
UNIT_LITERS = 'liters'
UNIT_KG = 'kg'

UNIT_CHOICES = [
    (UNIT_GRAMS, 'Grams'),
    (UNIT_CARATS, 'Carats'),
    (UNIT_PIECES, 'Pieces'),
    (UNIT_LITERS, 'Liters'),
    (UNIT_KG, 'Kilograms'),
]

# Metal type / purity choices — same values used on the Order form
METAL_TYPE_GOLD = 'Gold'
METAL_TYPE_SILVER = 'Silver'
METAL_TYPE_PLATINUM = 'Platinum'
METAL_TYPE_OTHER = 'Other'

METAL_TYPE_CHOICES = [
    ('', '— None —'),
    (METAL_TYPE_GOLD, 'Gold'),
    (METAL_TYPE_SILVER, 'Silver'),
    (METAL_TYPE_PLATINUM, 'Platinum'),
    (METAL_TYPE_OTHER, 'Other'),
]

PURITY_9K = '9K'
PURITY_10K = '10K'
PURITY_14K = '14K'
PURITY_18K = '18K'
PURITY_22K = '22K'
PURITY_24K = '24K'
PURITY_925 = '925Silver'
PURITY_950 = '950Platinum'
PURITY_OTHER = 'Other'

METAL_PURITY_CHOICES = [
    ('', '— None —'),
    (PURITY_9K, '9K'),
    (PURITY_10K, '10K'),
    (PURITY_14K, '14K'),
    (PURITY_18K, '18K'),
    (PURITY_22K, '22K'),
    (PURITY_24K, '24K'),
    (PURITY_925, '925 Silver'),
    (PURITY_950, '950 Platinum'),
    (PURITY_OTHER, 'Other'),
]

TRANSACTION_IN = 'IN'
TRANSACTION_OUT = 'OUT'
TRANSACTION_ADJUSTMENT = 'ADJUSTMENT'
TRANSACTION_WASTE = 'WASTE'

TRANSACTION_TYPE_CHOICES = [
    (TRANSACTION_IN, 'Stock In'),
    (TRANSACTION_OUT, 'Stock Out'),
    (TRANSACTION_ADJUSTMENT, 'Adjustment'),
    (TRANSACTION_WASTE, 'Waste'),
]


# ---------------------------------------------------------------------------
# MaterialCategory
# ---------------------------------------------------------------------------

class MaterialCategory(models.Model):
    GOLD = 'Gold'
    SILVER = 'Silver'
    PLATINUM = 'Platinum'
    GEMSTONES = 'Gemstones'
    CHEMICALS = 'Chemicals'
    TOOLS = 'Tools'
    PACKAGING = 'Packaging'

    CATEGORY_CHOICES = [
        (GOLD, 'Gold'),
        (SILVER, 'Silver'),
        (PLATINUM, 'Platinum'),
        (GEMSTONES, 'Gemstones'),
        (CHEMICALS, 'Chemicals'),
        (TOOLS, 'Tools'),
        (PACKAGING, 'Packaging'),
    ]

    name = models.CharField(
        max_length=100,
        choices=CATEGORY_CHOICES,
        unique=True,
        verbose_name='Category Name',
    )
    description = models.TextField(blank=True, verbose_name='Description')

    class Meta:
        verbose_name = 'Material Category'
        verbose_name_plural = 'Material Categories'
        ordering = ['name']

    def __str__(self):
        return self.name


# ---------------------------------------------------------------------------
# RawMaterial
# ---------------------------------------------------------------------------

class RawMaterial(models.Model):
    material_code = models.CharField(
        max_length=20,
        unique=True,
        blank=True,
        verbose_name='Material Code',
    )
    name = models.CharField(max_length=200, verbose_name='Material Name')
    category = models.ForeignKey(
        MaterialCategory,
        on_delete=models.PROTECT,
        related_name='materials',
        verbose_name='Category',
    )
    unit_of_measure = models.CharField(
        max_length=20,
        choices=UNIT_CHOICES,
        default=UNIT_GRAMS,
        verbose_name='Unit of Measure',
    )
    metal_type = models.CharField(
        max_length=20,
        choices=METAL_TYPE_CHOICES,
        blank=True,
        default='',
        verbose_name='Metal Type',
        help_text='Set for Gold, Silver, or Platinum materials to enable order stock checks.',
    )
    metal_purity = models.CharField(
        max_length=20,
        choices=METAL_PURITY_CHOICES,
        blank=True,
        default='',
        verbose_name='Metal Purity',
        help_text='e.g. 18K, 22K, 925 Silver. Must match the purity used on orders.',
    )
    description = models.TextField(blank=True, verbose_name='Description')
    minimum_stock_level = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        default=0,
        verbose_name='Minimum Stock Level',
        help_text='Alert is raised when stock falls below this level.',
    )
    is_active = models.BooleanField(default=True, verbose_name='Active')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Created At')

    class Meta:
        verbose_name = 'Raw Material'
        verbose_name_plural = 'Raw Materials'
        ordering = ['category', 'name']

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if not self.material_code:
            self.material_code = f'MAT-{self.pk:04d}'
            RawMaterial.objects.filter(pk=self.pk).update(material_code=self.material_code)

    def __str__(self):
        return f'[{self.material_code}] {self.name}'

    def get_current_stock(self):
        """Return current quantity on hand for this material, or 0 if no record exists."""
        try:
            return self.current_stock.quantity_on_hand
        except CurrentStock.DoesNotExist:
            return Decimal('0')

    @property
    def is_low_stock(self):
        return self.get_current_stock() < self.minimum_stock_level


# ---------------------------------------------------------------------------
# Supplier
# ---------------------------------------------------------------------------

class Supplier(models.Model):
    name = models.CharField(max_length=200, verbose_name='Supplier Name')
    contact_person = models.CharField(max_length=150, blank=True, verbose_name='Contact Person')
    phone = models.CharField(max_length=30, blank=True, verbose_name='Phone')
    email = models.EmailField(blank=True, verbose_name='Email')
    address = models.TextField(blank=True, verbose_name='Address')
    is_active = models.BooleanField(default=True, verbose_name='Active')

    class Meta:
        verbose_name = 'Supplier'
        verbose_name_plural = 'Suppliers'
        ordering = ['name']

    def __str__(self):
        return self.name


# ---------------------------------------------------------------------------
# StockEntry
# ---------------------------------------------------------------------------

class StockEntry(models.Model):
    material = models.ForeignKey(
        RawMaterial,
        on_delete=models.PROTECT,
        related_name='stock_entries',
        verbose_name='Material',
    )
    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='stock_entries',
        verbose_name='Supplier',
    )
    quantity = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        verbose_name='Quantity',
    )
    unit_cost = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        verbose_name='Unit Cost',
        help_text='Cost per unit of measure.',
    )
    total_cost = models.DecimalField(
        max_digits=16,
        decimal_places=4,
        editable=False,
        verbose_name='Total Cost',
    )
    entry_date = models.DateField(default=timezone.now, verbose_name='Entry Date')
    batch_number = models.CharField(max_length=100, blank=True, verbose_name='Batch Number')
    notes = models.TextField(blank=True, verbose_name='Notes')
    entered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='stock_entries',
        verbose_name='Entered By',
    )
    purity = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='Purity',
        help_text='For gold/silver: e.g. 18k, 22k, 24k, 925, 999.',
    )
    is_bulk = models.BooleanField(
        default=False,
        verbose_name='Bulk Entry',
        help_text='Indicates this entry was created via bulk CSV upload.',
    )

    class Meta:
        verbose_name = 'Stock Entry'
        verbose_name_plural = 'Stock Entries'
        ordering = ['-entry_date', '-id']

    def save(self, *args, **kwargs):
        self.total_cost = self.quantity * self.unit_cost
        super().save(*args, **kwargs)

    def __str__(self):
        return (
            f'{self.material.name} – {self.quantity} {self.material.unit_of_measure} '
            f'on {self.entry_date}'
        )


# ---------------------------------------------------------------------------
# StockTransaction
# ---------------------------------------------------------------------------

class StockTransaction(models.Model):
    material = models.ForeignKey(
        RawMaterial,
        on_delete=models.PROTECT,
        related_name='transactions',
        verbose_name='Material',
    )
    transaction_type = models.CharField(
        max_length=20,
        choices=TRANSACTION_TYPE_CHOICES,
        verbose_name='Transaction Type',
    )
    quantity = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        verbose_name='Quantity',
        help_text='Use positive values; direction is determined by transaction_type.',
    )
    reference_number = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Reference Number',
    )
    job_order = models.ForeignKey(
        'orders.JobOrder',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='stock_transactions',
        verbose_name='Job Order',
    )
    notes = models.TextField(blank=True, verbose_name='Notes')
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='stock_transactions',
        verbose_name='Created By',
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Created At')

    class Meta:
        verbose_name = 'Stock Transaction'
        verbose_name_plural = 'Stock Transactions'
        ordering = ['-created_at']

    def __str__(self):
        return (
            f'{self.get_transaction_type_display()} – {self.material.name} '
            f'x {self.quantity} ({self.created_at:%Y-%m-%d})'
        )


# ---------------------------------------------------------------------------
# CurrentStock
# ---------------------------------------------------------------------------

class CurrentStock(models.Model):
    material = models.OneToOneField(
        RawMaterial,
        on_delete=models.CASCADE,
        related_name='current_stock',
        verbose_name='Material',
    )
    quantity_on_hand = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        default=0,
        verbose_name='Quantity on Hand',
    )
    last_updated = models.DateTimeField(auto_now=True, verbose_name='Last Updated')

    class Meta:
        verbose_name = 'Current Stock'
        verbose_name_plural = 'Current Stocks'

    def __str__(self):
        return (
            f'{self.material.name}: {self.quantity_on_hand} '
            f'{self.material.unit_of_measure}'
        )
