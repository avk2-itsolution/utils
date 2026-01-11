from typing import Optional

from sync_utils.dataclass_compat import dataclass_compat as dataclass

from . import ExternalKey
from .sync_item_status import SyncItemStatus


@dataclass(frozen=True, slots=True)
class SyncItemState:
    key: ExternalKey
    version: Optional[str]
    status: SyncItemStatus
    attempts: int = 0
    last_error: Optional[str] = None
