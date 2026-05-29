from django.db import migrations, models


def populate_material_codes(apps, schema_editor):
    RawMaterial = apps.get_model('inventory', 'RawMaterial')
    for mat in RawMaterial.objects.order_by('pk'):
        mat.material_code = f'MAT-{mat.pk:04d}'
        mat.save(update_fields=['material_code'])


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0002_rawmaterial_metal_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='rawmaterial',
            name='material_code',
            field=models.CharField(blank=True, default='', max_length=20, verbose_name='Material Code'),
            preserve_default=False,
        ),
        migrations.RunPython(populate_material_codes, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='rawmaterial',
            name='material_code',
            field=models.CharField(max_length=20, unique=True, verbose_name='Material Code'),
        ),
    ]
