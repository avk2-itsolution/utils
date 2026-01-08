from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="SyncBinding",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("system", models.CharField(max_length=64)),
                ("ext_key", models.CharField(db_index=True, max_length=255)),
                ("internal_id", models.CharField(max_length=64)),
                ("version", models.CharField(blank=True, default="", max_length=128)),
            ],
            options={
                "db_table": "sync_binding",
                "unique_together": {("system", "ext_key")},
            },
        ),
        migrations.CreateModel(
            name="SyncCheckpoint",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("stream", models.CharField(max_length=128, unique=True)),
                ("token", models.CharField(max_length=256)),
            ],
            options={
                "db_table": "sync_checkpoint",
            },
        ),
        migrations.CreateModel(
            name="SyncItemState",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("system", models.CharField(max_length=64)),
                ("ext_key", models.CharField(db_index=True, max_length=255)),
                ("version", models.CharField(blank=True, default="", max_length=128)),
                ("status", models.CharField(max_length=32)),
                ("attempts", models.IntegerField(default=0)),
                ("last_error", models.TextField(blank=True, default="")),
            ],
            options={
                "db_table": "sync_item_state",
                "unique_together": {("system", "ext_key")},
            },
        ),
    ]
