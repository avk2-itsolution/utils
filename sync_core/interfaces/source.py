from typing import Protocol, Iterable, Optional, Generic

from ..dto import ExternalKey, Payload, Projection, Binding, KeyBinding
from ..dto.payload import TSource


class Source(Protocol[TSource]):
    """Источник изменений из внешней системы для одной синхронизируемой сущности."""

    def fetch(self, since_token: Optional[str]
              ) -> tuple[Iterable[tuple[ExternalKey, Payload[TSource]]], Optional[str]]:
        """Возвращает:
        - Iterable пар (ExternalKey, Payload) с изменениями после since_token
        - новый чекпоинт (token), который нужно сохранить в StateStore
        """
        ...  # отдаёт изменения пачками

    def validate(self, key: ExternalKey, payload: Payload[TSource]) -> None:
        """Проверяет техническую корректность данных источника, кидает SourceError при проблемах."""
        ...
