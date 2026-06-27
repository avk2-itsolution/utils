from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("bitrix_batch", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="bitrixbatchcommand",
            name="context",
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AddField(
            model_name="bitrixbatchcommand",
            name="error_payload",
            field=models.JSONField(blank=True, null=True),
        ),
    ]
