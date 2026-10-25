from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("bitrix_batch", "0002_bitrixbatchcommand_context_and_error_payload")]
    operations = [
        migrations.AddField(
            model_name="bitrixbatchcommand", name="before_send_path",
            field=models.CharField(blank=True, max_length=512, null=True),
        ),
        migrations.AlterField(
            model_name="bitrixbatchcommand", name="status",
            field=models.CharField(choices=[("pending", "Ожидает"), ("processing", "Обрабатывается"), ("success", "Успешно"), ("error", "Ошибка"), ("skipped", "Пропущено")], db_index=True, default="pending", max_length=32),
        ),
    ]
