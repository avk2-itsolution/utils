from typing import Protocol

from ..dto import ExternalKey, Payload, Projection
from ..dto.payload import TSource
from ..dto.projection import TTarget


class Mapper(Protocol[TSource, TTarget]):
    """Преобразует внешний Payload в Projection для внутренней системы.
    Должен кидать MappingError при бизнес-ошибках/некорректных данных.
    Должен кидать TargetError при ошибках записи в целевую систему."""

    def map(self, key: ExternalKey, payload: Payload[TSource]) -> Projection[TTarget]:
        """Строит Projection по внешнему ключу key и данным payload."""
        ...  # чистая функция: payload -> Projection

    def validate(self, key: ExternalKey, payload: Payload[TSource]) -> None:
        """Проверяет бизнес-корректность входных данных, кидает MappingError при нарушениях правил."""
        ...

