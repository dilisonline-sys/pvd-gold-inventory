from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0002_rebuild_orders'),
    ]

    operations = [
        migrations.AlterField(
            model_name='joborder',
            name='estimated_cost',
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                max_digits=14,
                null=True,
                verbose_name='Estimated Cost',
            ),
        ),
    ]
