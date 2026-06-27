import json
import time
from collections.abc import Callable
from datetime import timedelta
from math import ceil
from typing import Any

from django.db import models
from django.db.models import JSONField
from django.core.serializers.json import DjangoJSONEncoder
from django.utils import timezone
from django.utils.module_loading import import_string

from .querysets import BitrixBatchCommandQuerySet


class BitrixBatchCommand(models.Model):
    """Команда для batch-вызова Bitrix24."""

    class Status(models.TextChoices):
        PENDING = "pending", "Ожидает"
        PROCESSING = "processing", "Обрабатывается"
        SUCCESS = "success", "Успешно"
        ERROR = "error", "Ошибка"

    but = models.ForeignKey("bitrix24.BitrixUserToken", on_delete=models.PROTECT, related_name="queued_batch_commands")
    group_id = models.CharField(max_length=64, db_index=True, null=True, blank=True)
    method = models.CharField(max_length=255)
    params = JSONField(default=dict, blank=True)
    context = JSONField(default=dict, blank=True)
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.PENDING, db_index=True)
    result = JSONField(null=True, blank=True)
    error = models.TextField(null=True, blank=True)
    error_payload = JSONField(null=True, blank=True)
    callback_path = models.CharField(max_length=512, null=True, blank=True)
    callback_error = models.TextField(null=True, blank=True)
    callback_finished_at = models.DateTimeField(null=True, blank=True)
    attempts = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    processable_at = models.DateTimeField(default=timezone.now, db_index=True)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    objects = BitrixBatchCommandQuerySet.as_manager()

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"[{self.id}] {self.method} ({self.status})"

    @property
    def is_success(self) -> bool:
        return self.status == self.Status.SUCCESS

    @classmethod
    def enqueue(
        cls,
        *,
        but,
        method: str,
        params: dict[str, Any] | None = None,
        context: dict[str, Any] | None = None,
        group_id: str | None = None,
        delay_seconds: int = 0,
        callback: Callable[["BitrixBatchCommand"], None] | None = None,
    ) -> "BitrixBatchCommand":
        """Ставит команду в очередь."""
        if but is None or but.pk is None:
            raise ValueError("BitrixBatchCommand.enqueue requires saved BitrixUserToken")
        if delay_seconds < 0:
            raise ValueError("delay_seconds must be greater than or equal to 0")

        return cls.objects.create(
            but=but,
            group_id=group_id,
            method=method,
            params=cls._normalize_json_value(params or {}),
            context=cls._normalize_json_value(context or {}),
            processable_at=timezone.now() + timedelta(seconds=delay_seconds),
            callback_path=cls._get_callback_path(callback),
        )

    @classmethod
    def enqueue_many(
        cls,
        *,
        but,
        commands: list[dict[str, Any]],
        group_id: str | None = None,
        delay_seconds: int = 0,
    ) -> list["BitrixBatchCommand"]:
        """Ставит несколько команд в очередь."""
        result: list[BitrixBatchCommand] = []
        for command_data in commands:
            result.append(
                cls.enqueue(
                    but=but,
                    method=command_data["method"],
                    params=command_data.get("params"),
                    context=command_data.get("context"),
                    group_id=group_id,
                    delay_seconds=command_data.get("delay_seconds", delay_seconds),
                    callback=command_data.get("callback"),
                )
            )
        return result

    def mark_processing(self) -> None:
        """Помечает команду как обрабатываемую."""
        self.status = self.Status.PROCESSING
        self.started_at = timezone.now()
        self.finished_at = None
        self.error = None
        self.error_payload = None
        self.attempts += 1
        self.save(update_fields=["status", "started_at", "finished_at", "error", "error_payload", "attempts"])

    def mark_success(self, result: dict[str, Any] | None) -> None:
        """Сохраняет успешный результат."""
        self.status = self.Status.SUCCESS
        self.result = result
        self.error = None
        self.error_payload = None
        self.finished_at = timezone.now()
        self.save(update_fields=["status", "result", "error", "error_payload", "finished_at"])
        self.run_callback()

    def mark_error(self, error: str, error_payload: dict[str, Any] | None = None) -> None:
        """Сохраняет ошибку выполнения."""
        self.status = self.Status.ERROR
        self.result = None
        self.error = error
        self.error_payload = error_payload
        self.finished_at = timezone.now()
        self.save(update_fields=["status", "result", "error", "error_payload", "finished_at"])
        self.run_callback()

    def run_callback(self) -> None:
        """Запускает callback после завершения команды."""
        if not self.callback_path:
            return

        callback = import_string(self.callback_path)
        try:
            callback(self)
        except Exception as exc:
            self.callback_error = str(exc)
            self.callback_finished_at = timezone.now()
            self.save(update_fields=["callback_error", "callback_finished_at"])
            return

        self.callback_error = None
        self.callback_finished_at = timezone.now()
        self.save(update_fields=["callback_error", "callback_finished_at"])

    def wait_result(self, timeout: float = 30.0, poll_interval: float = 0.5) -> dict[str, Any] | None:
        """Ждёт завершения команды и возвращает результат."""

        started_at = time.monotonic()
        max_attempts = max(1, ceil(timeout / poll_interval))

        for attempt in range(max_attempts):
            self.refresh_from_db(fields=["status", "result", "error"])

            if self.status == self.Status.SUCCESS:
                return self.result

            if self.status == self.Status.ERROR:
                raise RuntimeError(self.error or f"Bitrix batch command {self.pk} failed")

            if attempt < max_attempts - 1:
                time.sleep(poll_interval)

        self.refresh_from_db(fields=["status", "result", "error"])
        if self.status == self.Status.SUCCESS:
            return self.result
        if self.status == self.Status.ERROR:
            raise RuntimeError(self.error or f"Bitrix batch command {self.pk} failed")

        elapsed = time.monotonic() - started_at
        raise TimeoutError(f"Bitrix batch command {self.pk} was not finished in {elapsed:.1f} seconds")

    def get_crm_item_id(self) -> str:
        """Возвращает id CRM item для crm.item.add/crm.item.update."""

        if self.method == "crm.item.add":
            return str(int(self.result["result"]["item"]["id"]))

        if self.method == "crm.item.update":
            return str(int(self.params["id"]))

        raise ValueError(f"Bitrix batch command {self.pk} does not support CRM item id extraction")

    def get_error_code(self) -> str | None:
        """Возвращает код ошибки Bitrix, если он есть."""

        if self.error_payload is None:
            return None
        if not isinstance(self.error_payload, dict):
            raise ValueError(f"Bitrix batch command {self.pk} error_payload must be dict")

        error_code = self.error_payload.get("error")
        if error_code is None:
            return None
        if not isinstance(error_code, str):
            raise ValueError(f"Bitrix batch command {self.pk} error code must be string")

        return error_code

    @staticmethod
    def _get_callback_path(callback: Callable[["BitrixBatchCommand"], None] | None) -> str | None:
        """Возвращает import path callback-функции."""
        if callback is None:
            return None
        if not callable(callback):
            raise TypeError("callback must be callable")

        module_name = getattr(callback, "__module__", None)
        qualname = getattr(callback, "__qualname__", None)
        if not module_name or not qualname or "<locals>" in qualname:
            raise ValueError("callback must be importable top-level function")

        return f"{module_name}.{qualname}"

    @staticmethod
    def _normalize_json_value(value: Any) -> Any:
        """Приводит значение к виду, совместимому с JSONField."""

        return json.loads(json.dumps(value, cls=DjangoJSONEncoder))
