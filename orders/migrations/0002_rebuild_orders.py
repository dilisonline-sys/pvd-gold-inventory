"""
Migration 0002: Rebuild the orders app from the old stub schema to the full schema.

The original 0001_initial created a minimal JobOrder table (customer_name, customer_phone,
customer_email flat fields, no Customer/ItemType FK, different status choices).

This migration:
  1. Drops the old orders_joborder table.
  2. Creates Customer, ItemType, JobOrder (full schema), and OrderNote.
"""

import decimal
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # -----------------------------------------------------------------
        # 1. Drop the old JobOrder table (was a stub with flat customer fields)
        # -----------------------------------------------------------------
        migrations.DeleteModel(
            name='JobOrder',
        ),

        # -----------------------------------------------------------------
        # 2. Create Customer
        # -----------------------------------------------------------------
        migrations.CreateModel(
            name='Customer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, verbose_name='Full Name')),
                ('phone', models.CharField(blank=True, max_length=30, verbose_name='Phone')),
                ('email', models.EmailField(blank=True, verbose_name='Email')),
                ('address', models.TextField(blank=True, verbose_name='Address')),
                ('notes', models.TextField(blank=True, verbose_name='Notes')),
                ('is_active', models.BooleanField(default=True, verbose_name='Active')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Created At')),
            ],
            options={
                'verbose_name': 'Customer',
                'verbose_name_plural': 'Customers',
                'ordering': ['name'],
            },
        ),

        # -----------------------------------------------------------------
        # 3. Create ItemType
        # -----------------------------------------------------------------
        migrations.CreateModel(
            name='ItemType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(
                    choices=[
                        ('Ring', 'Ring'),
                        ('Necklace', 'Necklace'),
                        ('Bracelet', 'Bracelet'),
                        ('Earring', 'Earring'),
                        ('Pendant', 'Pendant'),
                        ('Bangle', 'Bangle'),
                        ('Chain', 'Chain'),
                        ('Custom', 'Custom'),
                    ],
                    max_length=50,
                    unique=True,
                    verbose_name='Item Type',
                )),
                ('description', models.TextField(blank=True, verbose_name='Description')),
            ],
            options={
                'verbose_name': 'Item Type',
                'verbose_name_plural': 'Item Types',
                'ordering': ['name'],
            },
        ),

        # -----------------------------------------------------------------
        # 4. Create full JobOrder
        # -----------------------------------------------------------------
        migrations.CreateModel(
            name='JobOrder',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('order_number', models.CharField(
                    editable=False,
                    help_text='Auto-generated in format JO-YYYY-NNNN.',
                    max_length=20,
                    unique=True,
                    verbose_name='Order Number',
                )),
                ('description', models.TextField(verbose_name='Description / Specifications')),
                ('quantity', models.PositiveIntegerField(default=1, verbose_name='Quantity')),
                ('metal_type', models.CharField(
                    choices=[
                        ('Gold', 'Gold'),
                        ('Silver', 'Silver'),
                        ('Platinum', 'Platinum'),
                        ('Other', 'Other'),
                    ],
                    default='Gold',
                    max_length=20,
                    verbose_name='Metal Type',
                )),
                ('metal_purity', models.CharField(
                    choices=[
                        ('9K', '9K'),
                        ('10K', '10K'),
                        ('14K', '14K'),
                        ('18K', '18K'),
                        ('22K', '22K'),
                        ('24K', '24K'),
                        ('925Silver', '925 Silver'),
                        ('950Platinum', '950 Platinum'),
                        ('Other', 'Other'),
                    ],
                    default='18K',
                    max_length=20,
                    verbose_name='Metal Purity',
                )),
                ('estimated_weight', models.DecimalField(
                    decimal_places=4,
                    help_text='Estimated total weight in grams.',
                    max_digits=10,
                    verbose_name='Estimated Weight (g)',
                )),
                ('actual_weight', models.DecimalField(
                    blank=True,
                    decimal_places=4,
                    help_text='Actual total weight in grams, recorded on delivery.',
                    max_digits=10,
                    null=True,
                    verbose_name='Actual Weight (g)',
                )),
                ('stone_type', models.CharField(
                    blank=True,
                    help_text='e.g. Diamond, Ruby, Sapphire.',
                    max_length=100,
                    null=True,
                    verbose_name='Stone Type',
                )),
                ('stone_weight', models.DecimalField(
                    blank=True,
                    decimal_places=4,
                    max_digits=10,
                    null=True,
                    verbose_name='Stone Weight (carats)',
                )),
                ('special_instructions', models.TextField(blank=True, verbose_name='Special Instructions')),
                ('status', models.CharField(
                    choices=[
                        ('RECEIVED', 'Received'),
                        ('DESIGN', 'Design'),
                        ('IN_PRODUCTION', 'In Production'),
                        ('QC', 'Quality Control'),
                        ('READY', 'Ready for Delivery'),
                        ('DELIVERED', 'Delivered'),
                        ('CANCELLED', 'Cancelled'),
                    ],
                    default='RECEIVED',
                    max_length=20,
                    verbose_name='Status',
                )),
                ('priority', models.CharField(
                    choices=[
                        ('LOW', 'Low'),
                        ('MEDIUM', 'Medium'),
                        ('HIGH', 'High'),
                        ('URGENT', 'Urgent'),
                    ],
                    default='MEDIUM',
                    max_length=10,
                    verbose_name='Priority',
                )),
                ('order_date', models.DateField(default=django.utils.timezone.now, verbose_name='Order Date')),
                ('required_date', models.DateField(verbose_name='Required Date')),
                ('delivery_date', models.DateField(blank=True, null=True, verbose_name='Delivery Date')),
                ('estimated_cost', models.DecimalField(
                    decimal_places=2,
                    max_digits=14,
                    verbose_name='Estimated Cost',
                )),
                ('actual_cost', models.DecimalField(
                    blank=True,
                    decimal_places=2,
                    max_digits=14,
                    null=True,
                    verbose_name='Actual Cost',
                )),
                ('advance_payment', models.DecimalField(
                    decimal_places=2,
                    default=decimal.Decimal('0.00'),
                    max_digits=14,
                    verbose_name='Advance Payment',
                )),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Created At')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Updated At')),
                ('customer', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name='job_orders',
                    to='orders.customer',
                    verbose_name='Customer',
                )),
                ('item_type', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name='job_orders',
                    to='orders.itemtype',
                    verbose_name='Item Type',
                )),
                ('created_by', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name='job_orders_created',
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='Created By',
                )),
            ],
            options={
                'verbose_name': 'Job Order',
                'verbose_name_plural': 'Job Orders',
                'ordering': ['-created_at'],
            },
        ),

        # -----------------------------------------------------------------
        # 5. Create OrderNote
        # -----------------------------------------------------------------
        migrations.CreateModel(
            name='OrderNote',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('note', models.TextField(verbose_name='Note')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Created At')),
                ('order', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='notes',
                    to='orders.joborder',
                    verbose_name='Job Order',
                )),
                ('added_by', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name='order_notes',
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='Added By',
                )),
            ],
            options={
                'verbose_name': 'Order Note',
                'verbose_name_plural': 'Order Notes',
                'ordering': ['-created_at'],
            },
        ),
    ]
