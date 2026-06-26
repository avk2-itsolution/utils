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

    def lock_pending(self):
        """Блокирует необработанные команды."""
        locked_commands = self.select_for_update(skip_locked=True).pending().ordered_for_processing()
        if locked_commands.first() is None:
            return self.none()

        return locked_commands
