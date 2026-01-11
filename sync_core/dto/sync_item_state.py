from typing import Optional
from dataclasses import dataclass

from . import ExternalKey
from .sync_item_status import SyncItemStatus


@dataclass(frozen=True)
class SyncItemState:
    key: ExternalKey
    version: Optional[str]
    status: SyncItemStatus
    attempts: int = 0
    last_error: Optional[str] = None
