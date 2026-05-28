import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("manufacturing", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="processrecord",
            name="created_at",
            field=models.DateTimeField(
                auto_now_add=True,
                default=django.utils.timezone.now,
                verbose_name="Created At",
            ),
            preserve_default=False,
        ),
        migrations.AlterModelOptions(
            name="processrecord",
            options={
                "ordering": ["-created_at"],
                "verbose_name": "Process Record",
                "verbose_name_plural": "Process Records",
            },
        ),
    ]
