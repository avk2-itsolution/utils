import typing
from dataclasses import dataclass, replace
from datetime import datetime


@dataclass(frozen=True, slots=True)
class SyncResult:
    created: int = 0
    updated: int = 0
    skipped: int = 0
    failed: int = 0
    started_at: datetime = datetime.utcnow()  # при необходимости можно заменить на default_factory  # TODO

    def inc(self, *, created: int = 0, updated: int = 0, skipped: int = 0, failed: int = 0,
            ) -> typing.Self:
        """Возвращает новый SyncResult с увеличенными счётчиками."""
        return replace(
            self,
            created=self.created + created,
            updated=self.updated + updated,
            skipped=self.skipped + skipped,
            failed=self.failed + failed,
        )


