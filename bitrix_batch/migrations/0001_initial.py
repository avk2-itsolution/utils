from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("bitrix24", "0006_auto_20240528_1411"),
    ]

    operations = [
        migrations.CreateModel(
            name="BitrixBatchCommand",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("group_id", models.CharField(blank=True, db_index=True, max_length=64, null=True)),
                ("method", models.CharField(max_length=255)),
                ("params", models.JSONField(blank=True, default=dict)),
                ("status", models.CharField(choices=[("pending", "Ожидает"), ("processing", "Обрабатывается"), ("success", "Успешно"), ("error", "Ошибка")], db_index=True, default="pending", max_length=32)),
                ("result", models.JSONField(blank=True, null=True)),
                ("error", models.TextField(blank=True, null=True)),
                ("callback_path", models.CharField(blank=True, max_length=512, null=True)),
                ("callback_error", models.TextField(blank=True, null=True)),
                ("callback_finished_at", models.DateTimeField(blank=True, null=True)),
                ("attempts", models.PositiveIntegerField(default=0)),
                ("created_at", models.DateTimeField(db_index=True, default=django.utils.timezone.now)),
                ("processable_at", models.DateTimeField(db_index=True, default=django.utils.timezone.now)),
                ("started_at", models.DateTimeField(blank=True, null=True)),
                ("finished_at", models.DateTimeField(blank=True, null=True)),
                ("but", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="queued_batch_commands", to="bitrix24.bitrixusertoken")),
            ],
            options={"ordering": ["id"]},
        ),
    ]
