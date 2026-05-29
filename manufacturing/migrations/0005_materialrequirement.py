from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0001_initial'),
        ('manufacturing', '0004_finalproduct_optional_job'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='MaterialRequirement',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity_required', models.DecimalField(decimal_places=4, max_digits=12, verbose_name='Quantity Required')),
                ('notes', models.CharField(blank=True, max_length=200, verbose_name='Notes')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='material_requirements_created', to=settings.AUTH_USER_MODEL, verbose_name='Added By')),
                ('material', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='material_requirements', to='inventory.rawmaterial', verbose_name='Material')),
                ('production_job', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='material_requirements', to='manufacturing.productionjob', verbose_name='Production Job')),
            ],
            options={
                'verbose_name': 'Material Requirement',
                'verbose_name_plural': 'Material Requirements',
                'ordering': ['material__category__name', 'material__name'],
            },
        ),
    ]
