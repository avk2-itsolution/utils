from dataclasses import dataclass
from typing import Optional

from utils.sync_core.dto import ExternalKey
from utils.sync_core.dto.sync_item_status import SyncItemStatus


@dataclass(frozen=True, slots=True)
class SyncItemState:
    key: ExternalKey
    version: Optional[str]
    status: SyncItemStatus
    attempts: int = 0
    last_error: Optional[str] = None
