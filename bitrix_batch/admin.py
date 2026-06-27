from django import forms
from django.contrib import admin

from prettyjson import PrettyJSONWidget

from utils.bitrix_batch.models import BitrixBatchCommand


class BitrixBatchCommandAdminForm(forms.ModelForm):
    class Meta:
        model = BitrixBatchCommand
        fields = "__all__"
        widgets = {
            "params": PrettyJSONWidget(attrs={"initial": "parsed"}),
            "context": PrettyJSONWidget(attrs={"initial": "parsed"}),
            "result": PrettyJSONWidget(attrs={"initial": "parsed"}),
            "error_payload": PrettyJSONWidget(attrs={"initial": "parsed"}),
        }


@admin.register(BitrixBatchCommand)
class BitrixBatchCommandAdmin(admin.ModelAdmin):
    form = BitrixBatchCommandAdminForm
    readonly_fields = ["id", "created_at", "started_at", "finished_at"]
    list_display = ("id", "but", "method", "status", "attempts", "created_at", "finished_at")
    list_display_links = list_display
    list_filter = ("status", "but")
    search_fields = ("method", "group_id", "error")
    raw_id_fields = ["but"]
