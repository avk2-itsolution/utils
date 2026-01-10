from typing import Protocol, Iterable, Optional, Callable, TypeVar

from ..dto import ExternalKey, Payload, Projection, Binding, KeyBinding
from ..dto.payload import TSource


CheckpointValue = Optional[str]
DeferredCheckpoint = Callable[[], Optional[str]]
FetchedItems = Iterable[tuple[ExternalKey, Payload[TSource]]]
FetchResult = tuple[FetchedItems, CheckpointValue | DeferredCheckpoint]


class Source(Protocol[TSource]):
    """Источник изменений из внешней системы для одной синхронизируемой сущности."""

    def fetch(self, since_token: Optional[str]) -> FetchResult:
        """Возвращает:
        - Iterable пар (ExternalKey, Payload) с изменениями после since_token
        - новый чекпоинт (token), который нужно сохранить в StateStore.
          Можно вернуть отложенный чекпоинт как callable, если он вычисляется после обхода итератора.
        """
        ...  # отдаёт изменения пачками

    def validate(self, key: ExternalKey, payload: Payload[TSource]) -> None:
        """Проверяет техническую корректность данных источника, кидает SourceError при проблемах."""
        ...
