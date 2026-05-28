import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("manufacturing", "0002_processrecord_created_at"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="FinalProduct",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=200, verbose_name="Product Name")),
                ("description", models.TextField(blank=True, verbose_name="Description")),
                ("metal_type", models.CharField(blank=True, max_length=100, verbose_name="Metal Type")),
                ("purity", models.CharField(blank=True, max_length=20, verbose_name="Purity / Karat")),
                ("final_weight", models.DecimalField(blank=True, decimal_places=4, max_digits=10, null=True, verbose_name="Final Weight (g)")),
                ("finish", models.CharField(choices=[("POLISHED", "High Polish"), ("MATTE", "Matte"), ("BRUSHED", "Brushed"), ("HAMMERED", "Hammered"), ("SANDBLAST", "Sandblast"), ("OTHER", "Other")], default="POLISHED", max_length=20, verbose_name="Surface Finish")),
                ("stone_details", models.TextField(blank=True, verbose_name="Stone / Gem Details")),
                ("hallmark", models.CharField(blank=True, max_length=100, verbose_name="Hallmark / Stamp")),
                ("image", models.ImageField(blank=True, null=True, upload_to="final_products/", verbose_name="Product Photo")),
                ("notes", models.TextField(blank=True, verbose_name="Additional Notes")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Recorded At")),
                ("created_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="final_products_recorded", to=settings.AUTH_USER_MODEL, verbose_name="Recorded By")),
                ("production_job", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="final_product", to="manufacturing.productionjob", verbose_name="Production Job")),
            ],
            options={"verbose_name": "Final Product", "verbose_name_plural": "Final Products", "ordering": ["-created_at"]},
        ),
    ]
