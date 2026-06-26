from django.contrib import admin

import django
if django.VERSION[0] >= 4:
    from django.db.models import JSONField
else:
    from django.contrib.postgres.fields import JSONField

from prettyjson import PrettyJSONWidget

from utils.bitrix_batch.models import BitrixBatchCommand


@admin.register(BitrixBatchCommand)
class BitrixBatchCommandAdmin(admin.ModelAdmin):
    formfield_overrides = {
        JSONField: {"widget": PrettyJSONWidget},
    }
    readonly_fields = ["id", "created_at", "started_at", "finished_at"]
    list_display = ("id", "but", "method", "status", "attempts", "created_at", "finished_at")
    list_display_links = list_display
    list_filter = ("status", "but")
    search_fields = ("method", "group_id", "error")
    raw_id_fields = ["but"]
