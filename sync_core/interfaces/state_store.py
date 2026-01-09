from typing import Protocol, Iterable, Optional

from ..dto import ExternalKey, Binding, KeyBinding, SyncItemState


class StateStore(Protocol):
    """Хранит чекпоинты синка и связи ExternalKey ↔ internal_id/версия."""
    """
    типы чекпоинтов:
    updated_at (ISO-время)
    Монотонный id
    Cursor/next_page_token от API
    """

    def get_checkpoint(self, stream: str) -> Optional[str]:
        """Возвращает сохранённый чекпоинт для потока stream."""
        ...

    def save_checkpoint(self, stream: str, token: str) -> None:
        """Сохраняет чекпоинт token для потока stream."""
        ...

    def bind(self, key: ExternalKey, internal_id: str, version: Optional[str]) -> None:
        """Связывает внешний ключ key с internal_id и версией version."""
        ...

    def get_binding(self, key: ExternalKey) -> Optional[Binding]:
        """Возвращает Binding по внешнему ключу key, если связь есть."""
        ...

    def iter_bindings(self, system: str) -> Iterable[KeyBinding]:
        """Итерация по всем биндингам для системы (нужно для поиска удалённых во внешнем снапшоте)."""
        ...

    def validate_binding(self, key: ExternalKey, binding: Binding) -> None:
        """Проверяет консистентность биндинга, кидает StateError (например, битый internal_id/версия)."""
        ...

    def get_item_state(self, key: ExternalKey) -> Optional[SyncItemState]:
        """Возвращает сохранённое состояние обработки по ключу, если есть."""
        ...

    def save_item_state(self, state: SyncItemState) -> None:
        """Сохраняет/обновляет состояние обработки по ключу."""
        ...
