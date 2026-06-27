import traceback

from ..dto import ExternalKey
from ..errors import SyncError
from ..interfaces import SyncLogger


class BaseSyncLogger(SyncLogger):
    """Базовый логгер событий синхронизации."""

    def __init__(self, *, error_place: str = "sync_core"):
        self.error_place = error_place

    def on_skipped(self, key: ExternalKey, reason: str) -> None:
        from utils.admin_logger.models import Log

        Log.warning(f"[skip] {key} {reason}", error_place=self.error_place)

    def on_created(self, key: ExternalKey, internal_id: str) -> None:
        from utils.admin_logger.models import Log

        Log.warning(f"[create] {key} -> {internal_id}", error_place=self.error_place)

    def on_updated(self, key: ExternalKey, internal_id: str) -> None:
        from utils.admin_logger.models import Log

        Log.warning(f"[update] {key} -> {internal_id}", error_place=self.error_place)

    def on_deleted(self, key: ExternalKey, internal_id: str) -> None:
        from utils.admin_logger.models import Log

        Log.warning(f"[delete] {key} -> {internal_id}", error_place=self.error_place)

    def on_error(self, key: ExternalKey, exc: SyncError) -> None:
        from utils.admin_logger.models import Log

        Log.error(
            f"[error] {key} {exc}",
            error_place=self.error_place,
            traceback_text=traceback.format_exc(),
        )
