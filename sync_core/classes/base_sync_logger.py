from functions1 import debug_point_async
from sync_core.dto import ExternalKey
from sync_core.errors import SyncError
from sync_core.interfaces import SyncLogger


class BaseSyncLogger(SyncLogger):
    """Базовая реализация логирования событий синхронизации."""

    def on_skipped(self, key: ExternalKey, reason: str) -> None:
        debug_point_async(f"[skip] {key} {reason}", with_tags=False, with_traceback=False)

    def on_created(self, key: ExternalKey, internal_id: str) -> None:
        debug_point_async(f"[create] {key} -> {internal_id}", with_tags=False, with_traceback=False)

    def on_updated(self, key: ExternalKey, internal_id: str) -> None:
        debug_point_async(f"[update] {key} -> {internal_id}", with_tags=False, with_traceback=False)

    def on_deleted(self, key: ExternalKey, internal_id: str) -> None:
        debug_point_async(f"[delete] {key} -> {internal_id}", with_tags=False, with_traceback=False)

    def on_error(self, key: ExternalKey, exc: SyncError) -> None:
        debug_point_async(f"[error] {key} {exc}", with_tags=True, with_traceback=True)
