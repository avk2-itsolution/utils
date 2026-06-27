from typing import Protocol, Optional

from ..dto import Binding, ExternalKey, Projection, TargetUpsertResult
from ..dto.projection import TTarget


class Target(Protocol[TTarget]):
    """Приёмник, выполняющий upsert проекций во внутреннюю систему."""

    def upsert(
            self, key: ExternalKey, projection: Projection[TTarget], binding: Optional[Binding] = None, version: str | None = None
    ) -> TargetUpsertResult:
        """Создаёт/обновляет сущность по projection и возвращает TargetUpsertResult.
        binding — сохранённый Binding для ключа, если он есть.
        """
        ...  # возвращает внутренний id

    def delete(self, key: ExternalKey, binding: Binding) -> None:
        """Удаляет/архивирует сущность в целевой системе по биндингу."""
        ...

    def validate(self, key: ExternalKey, projection: Projection[TTarget]) -> None:
        """Проверяет, что проекция пригодна для записи в целевую систему, кидает TargetError."""
        ...
