from django.contrib import admin
from django.db import models


class AbstractSyncBinding(models.Model):
    system = models.CharField(max_length=64)
    ext_key = models.CharField(max_length=255, db_index=True)
    internal_id = models.CharField(max_length=64)
    version = models.CharField(max_length=128, blank=True, default="")

    class Meta:
        abstract = True
        unique_together = (("system", "ext_key"),)

    class Admin(admin.ModelAdmin):
        list_display = ("system", "ext_key", "internal_id", "version")


class AbstractSyncCheckpoint(models.Model):
    stream = models.CharField(max_length=128, unique=True)
    token = models.CharField(max_length=256)

    class Meta:
        abstract = True

    class Admin(admin.ModelAdmin):
        list_display = ("stream", "token",)


class AbstractSyncItemState(models.Model):
    system = models.CharField(max_length=64)
    ext_key = models.CharField(max_length=255, db_index=True)
    version = models.CharField(max_length=128, blank=True, default="")
    status = models.CharField(max_length=32)
    attempts = models.IntegerField(default=0)
    last_error = models.TextField(blank=True, default="")

    class Meta:
        abstract = True
        unique_together = (("system", "ext_key"),)

    class Admin(admin.ModelAdmin):
        list_display = ("system", "ext_key", "status", "version", "attempts", "last_error")


class SyncBinding(AbstractSyncBinding):
    class Meta(AbstractSyncBinding.Meta):
        db_table = "sync_binding"


class SyncCheckpoint(AbstractSyncCheckpoint):
    class Meta(AbstractSyncCheckpoint.Meta):
        db_table = "sync_checkpoint"


class SyncItemState(AbstractSyncItemState):
    class Meta(AbstractSyncItemState.Meta):
        db_table = "sync_item_state"
