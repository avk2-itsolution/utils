from dataclasses import dataclass

from django.db import transaction

from integration_utils.bitrix24.exceptions import BatchApiCallError
from utils.bitrix_batch.models import BitrixBatchCommand


DEFAULT_BATCH_TIMEOUT = 240


def process_pending_bitrix_batch_commands(timeout: int = DEFAULT_BATCH_TIMEOUT) -> int:
    """Берёт необработанные команды, шлёт их батчами и сохраняет результаты."""
    processed_callbacks = _process_pending_callbacks()
    pending_commands: list[BitrixBatchCommand] = _lock_pending_commands()
    if not pending_commands:
        return processed_callbacks

    batch = BitrixCommandBatch.fabric(pending_commands, timeout=timeout)
    return processed_callbacks + batch.process()


def _lock_pending_commands() -> list[BitrixBatchCommand]:
    """Берёт и помечает pending-команды."""
    with transaction.atomic():
        commands: list[BitrixBatchCommand] = []
        queryset = BitrixBatchCommand.objects.lock_pending().for_batch_processing()
        for command in queryset.iterator():
            command.mark_processing()
            commands.append(command)

        return commands


def _process_pending_callbacks() -> int:
    """Дозапускает callback у уже завершённых команд."""
    with transaction.atomic():
        commands = list(
            BitrixBatchCommand.objects
            .lock_callback_pending()
            .for_callback_processing()
            .iterator()
        )

    for command in commands:
        command.run_callback()

    return len(commands)


@dataclass
class BitrixCommandBatch:
    """Набор команд для batch-обработки."""

    commands: list[BitrixBatchCommand]
    timeout: int

    @classmethod
    def fabric(cls, commands: list[BitrixBatchCommand], *, timeout: int) -> "BitrixCommandBatch":
        """Создаёт объект обработки из списка команд."""
        return cls(commands=commands, timeout=timeout)

    @property
    def but(self):
        return self.commands[0].but

    def process(self) -> int:
        """Отправляет команды и сохраняет результаты."""
        if not self.commands:
            return 0

        try:
            batch_result = self.but.batch_api_call(
                [
                    (str(command.id), command.method, command.params)
                    for command in self.commands
                ],
                timeout=self.timeout,
            )
        except BatchApiCallError as exc:
            for command in self.commands:
                command.mark_error(str(exc))
            return len(self.commands)
        except Exception as exc:
            for command in self.commands:
                command.mark_error(str(exc))
            return len(self.commands)

        for command in self.commands:
            if str(command.id) in batch_result.successes:
                command.mark_success(batch_result.successes[str(command.id)])
            elif str(command.id) in batch_result.errors:
                error_payload = batch_result.errors[str(command.id)]
                command.mark_error(str(error_payload), error_payload=error_payload)
            else:
                command.mark_error("No batch result returned from Bitrix")

        return len(self.commands)
