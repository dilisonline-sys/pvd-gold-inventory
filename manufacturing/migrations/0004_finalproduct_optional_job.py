from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('manufacturing', '0003_finalproduct'),
    ]

    operations = [
        migrations.AddField(
            model_name='finalproduct',
            name='job_ref',
            field=models.CharField(
                blank=True,
                help_text='Manual job/order reference when not linked to a production job.',
                max_length=50,
                verbose_name='Job Reference',
            ),
        ),
        migrations.AlterField(
            model_name='finalproduct',
            name='production_job',
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='final_product',
                to='manufacturing.productionjob',
                verbose_name='Production Job',
            ),
        ),
    ]
