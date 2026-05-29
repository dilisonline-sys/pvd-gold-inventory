from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils import timezone


# ---------------------------------------------------------------------------
# Choices
# ---------------------------------------------------------------------------

METAL_TYPE_GOLD = 'Gold'
METAL_TYPE_SILVER = 'Silver'
METAL_TYPE_PLATINUM = 'Platinum'
METAL_TYPE_OTHER = 'Other'

METAL_TYPE_CHOICES = [
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

STATUS_RECEIVED = 'RECEIVED'
STATUS_DESIGN = 'DESIGN'
STATUS_IN_PRODUCTION = 'IN_PRODUCTION'
STATUS_QC = 'QC'
STATUS_READY = 'READY'
STATUS_DELIVERED = 'DELIVERED'
STATUS_CANCELLED = 'CANCELLED'

ORDER_STATUS_CHOICES = [
    (STATUS_RECEIVED, 'Received'),
    (STATUS_DESIGN, 'Design'),
    (STATUS_IN_PRODUCTION, 'In Production'),
    (STATUS_QC, 'Quality Control'),
    (STATUS_READY, 'Ready for Delivery'),
    (STATUS_DELIVERED, 'Delivered'),
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


# ---------------------------------------------------------------------------
# Customer
# ---------------------------------------------------------------------------

class Customer(models.Model):
    """A customer who places jewelry job orders."""

    name = models.CharField(max_length=200, verbose_name='Full Name')
    phone = models.CharField(max_length=30, blank=True, verbose_name='Phone')
    email = models.EmailField(blank=True, verbose_name='Email')
    address = models.TextField(blank=True, verbose_name='Address')
    notes = models.TextField(blank=True, verbose_name='Notes')
    is_active = models.BooleanField(default=True, verbose_name='Active')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Created At')

    class Meta:
        verbose_name = 'Customer'
        verbose_name_plural = 'Customers'
        ordering = ['name']

    def __str__(self):
        return self.name


# ---------------------------------------------------------------------------
# ItemType
# ---------------------------------------------------------------------------

class ItemType(models.Model):
    """Category of jewelry item (Ring, Necklace, etc.)."""

    RING = 'Ring'
    NECKLACE = 'Necklace'
    BRACELET = 'Bracelet'
    EARRING = 'Earring'
    PENDANT = 'Pendant'
    BANGLE = 'Bangle'
    CHAIN = 'Chain'
    CUSTOM = 'Custom'

    ITEM_TYPE_CHOICES = [
        (RING, 'Ring'),
        (NECKLACE, 'Necklace'),
        (BRACELET, 'Bracelet'),
        (EARRING, 'Earring'),
        (PENDANT, 'Pendant'),
        (BANGLE, 'Bangle'),
        (CHAIN, 'Chain'),
        (CUSTOM, 'Custom'),
    ]

    name = models.CharField(
        max_length=50,
        choices=ITEM_TYPE_CHOICES,
        unique=True,
        verbose_name='Item Type',
    )
    description = models.TextField(blank=True, verbose_name='Description')

    class Meta:
        verbose_name = 'Item Type'
        verbose_name_plural = 'Item Types'
        ordering = ['name']

    def __str__(self):
        return self.name


# ---------------------------------------------------------------------------
# JobOrder
# ---------------------------------------------------------------------------

class JobOrder(models.Model):
    """Main order model representing a customer's jewelry manufacturing request."""

    order_number = models.CharField(
        max_length=20,
        unique=True,
        editable=False,
        verbose_name='Order Number',
        help_text='Auto-generated in format JO-YYYY-NNNN.',
    )
    customer = models.ForeignKey(
        Customer,
        on_delete=models.PROTECT,
        related_name='job_orders',
        verbose_name='Customer',
    )
    item_type = models.ForeignKey(
        ItemType,
        on_delete=models.PROTECT,
        related_name='job_orders',
        verbose_name='Item Type',
    )
    description = models.TextField(verbose_name='Description / Specifications')
    quantity = models.PositiveIntegerField(default=1, verbose_name='Quantity')
    metal_type = models.CharField(
        max_length=20,
        choices=METAL_TYPE_CHOICES,
        default=METAL_TYPE_GOLD,
        verbose_name='Metal Type',
    )
    metal_purity = models.CharField(
        max_length=20,
        choices=METAL_PURITY_CHOICES,
        default=PURITY_18K,
        verbose_name='Metal Purity',
    )
    estimated_weight = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        verbose_name='Estimated Weight (g)',
        help_text='Estimated total weight in grams.',
    )
    actual_weight = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        null=True,
        blank=True,
        verbose_name='Actual Weight (g)',
        help_text='Actual total weight in grams, recorded on delivery.',
    )
    stone_type = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='Stone Type',
        help_text='e.g. Diamond, Ruby, Sapphire.',
    )
    stone_weight = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        null=True,
        blank=True,
        verbose_name='Stone Weight (carats)',
    )
    special_instructions = models.TextField(
        blank=True,
        verbose_name='Special Instructions',
    )
    status = models.CharField(
        max_length=20,
        choices=ORDER_STATUS_CHOICES,
        default=STATUS_RECEIVED,
        verbose_name='Status',
    )
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default=PRIORITY_MEDIUM,
        verbose_name='Priority',
    )
    order_date = models.DateField(default=timezone.now, verbose_name='Order Date')
    required_date = models.DateField(verbose_name='Required Date')
    delivery_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='Delivery Date',
    )
    estimated_cost = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Estimated Cost',
    )
    actual_cost = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Actual Cost',
    )
    advance_payment = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='Advance Payment',
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='job_orders_created',
        verbose_name='Created By',
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Created At')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Updated At')

    class Meta:
        verbose_name = 'Job Order'
        verbose_name_plural = 'Job Orders'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.order_number} – {self.customer.name}'

    # ------------------------------------------------------------------
    # Order number generation
    # ------------------------------------------------------------------

    def generate_order_number(self):
        year = timezone.now().year
        prefix = f'JO-{year}-'
        last = (
            JobOrder.objects
            .filter(order_number__startswith=prefix)
            .order_by('order_number')
            .last()
        )
        if last:
            try:
                seq = int(last.order_number.split('-')[-1]) + 1
            except (ValueError, IndexError):
                seq = 1
        else:
            seq = 1
        return f'{prefix}{seq:04d}'

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = self.generate_order_number()
        super().save(*args, **kwargs)

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def balance_due(self):
        """Balance due = (actual_cost or estimated_cost) minus advance_payment."""
        cost = self.actual_cost if self.actual_cost is not None else self.estimated_cost
        if cost is None:
            return Decimal('0.00')
        return cost - self.advance_payment

    @property
    def is_overdue(self):
        if self.status in (STATUS_DELIVERED, STATUS_CANCELLED):
            return False
        return timezone.now().date() > self.required_date


# ---------------------------------------------------------------------------
# OrderNote
# ---------------------------------------------------------------------------

class OrderNote(models.Model):
    """A timestamped note attached to a JobOrder."""

    order = models.ForeignKey(
        JobOrder,
        on_delete=models.CASCADE,
        related_name='notes',
        verbose_name='Job Order',
    )
    note = models.TextField(verbose_name='Note')
    added_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='order_notes',
        verbose_name='Added By',
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Created At')

    class Meta:
        verbose_name = 'Order Note'
        verbose_name_plural = 'Order Notes'
        ordering = ['-created_at']

    def __str__(self):
        return (
            f'Note on {self.order.order_number} by {self.added_by} '
            f'at {self.created_at:%Y-%m-%d %H:%M}'
        )
