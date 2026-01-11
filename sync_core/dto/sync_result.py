import typing
from dataclasses import replace, dataclass
from datetime import datetime
from typing import TypeVar

SelfSyncResult = TypeVar("SelfSyncResult", bound="SyncResult")


@dataclass(frozen=True)
class SyncResult:
    created: int = 0
    updated: int = 0
    skipped: int = 0
    failed: int = 0
    started_at: datetime = datetime.utcnow()  # при необходимости можно заменить на default_factory  # TODO

    def inc(self, *, created: int = 0, updated: int = 0, skipped: int = 0, failed: int = 0,
            ) -> SelfSyncResult:
        """Возвращает новый SyncResult с увеличенными счётчиками."""
        return replace(
            self,
            created=self.created + created,
            updated=self.updated + updated,
            skipped=self.skipped + skipped,
            failed=self.failed + failed,
        )


