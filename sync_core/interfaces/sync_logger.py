from typing import Protocol
from ..dto import ExternalKey
from ..errors import SyncError


class SyncLogger(Protocol):
    """Контракт логирования событий синхронизации."""

    def on_skipped(self, key: ExternalKey, reason: str) -> None: ...

    def on_created(self, key: ExternalKey, internal_id: str) -> None: ...

    def on_updated(self, key: ExternalKey, internal_id: str) -> None: ...

    def on_deleted(self, key: ExternalKey, internal_id: str) -> None: ...

    def on_error(self, key: ExternalKey, exc: SyncError) -> None: ...
