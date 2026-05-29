from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='rawmaterial',
            name='metal_type',
            field=models.CharField(
                blank=True,
                choices=[
                    ('', '— None —'),
                    ('Gold', 'Gold'),
                    ('Silver', 'Silver'),
                    ('Platinum', 'Platinum'),
                    ('Other', 'Other'),
                ],
                default='',
                max_length=20,
                verbose_name='Metal Type',
                help_text='Set for Gold, Silver, or Platinum materials to enable order stock checks.',
            ),
        ),
        migrations.AddField(
            model_name='rawmaterial',
            name='metal_purity',
            field=models.CharField(
                blank=True,
                choices=[
                    ('', '— None —'),
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
                default='',
                max_length=20,
                verbose_name='Metal Purity',
                help_text='e.g. 18K, 22K, 925 Silver. Must match the purity used on orders.',
            ),
        ),
    ]
