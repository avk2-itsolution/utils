from django.utils import timezone

from django.db import models


class BitrixBatchCommandQuerySet(models.QuerySet):
    """QuerySet очереди batch-команд Bitrix24."""

    def pending(self):
        """Возвращает необработанные команды."""
        return self.filter(
            status=self.model.Status.PENDING,
            processable_at__lte=timezone.now(),
        )

    def ordered_for_processing(self):
        """Сортирует команды для batch-обработки."""
        return self.select_related("but").order_by("id")

    def finished(self):
        """Возвращает уже завершённые команды."""
        return self.filter(
            status__in=[self.model.Status.SUCCESS, self.model.Status.ERROR],
        )

    def callback_pending(self):
        """Возвращает команды с незавершённым callback."""
        return self.exclude(callback_path__isnull=True).exclude(callback_path="").filter(
            callback_finished_at__isnull=True,
        )

    def lock_pending(self):
        """Блокирует необработанные команды."""
        locked_commands = self.select_for_update(skip_locked=True).pending().ordered_for_processing()
        if locked_commands.first() is None:
            return self.none()

        return locked_commands

    def lock_callback_pending(self):
        """Блокирует завершённые команды с незавершённым callback."""
        locked_commands = self.select_for_update(skip_locked=True).finished().callback_pending().ordered_for_processing()
        if locked_commands.first() is None:
            return self.none()

        return locked_commands
