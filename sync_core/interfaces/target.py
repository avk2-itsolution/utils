from typing import Protocol

from utils.sync_core.dto import ExternalKey, Projection, Binding
from utils.sync_core.dto.projection import TTarget


class Target(Protocol[TTarget]):
    """Приёмник, выполняющий upsert проекций во внутреннюю систему."""

    def upsert(self, key: ExternalKey, projection: Projection[TTarget], *, binding: Binding | None = None) -> str:
        """Создаёт/обновляет сущность по projection, связав её с key, и возвращает internal_id.
        binding — сохранённый Binding для ключа, если он есть (используется для различения create/update).
        """
        ...  # возвращает внутренний id

    def delete(self, key: ExternalKey, binding: Binding) -> None:
        """Удаляет/архивирует сущность в целевой системе по биндингу."""
        ...

    def validate(self, key: ExternalKey, projection: Projection[TTarget]) -> None:
        """Проверяет, что проекция пригодна для записи в целевую систему, кидает TargetError."""
        ...
