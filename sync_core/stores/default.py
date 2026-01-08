from utils.sync_core.models import SyncBinding, SyncCheckpoint, SyncItemState
from utils.sync_core.stores.base import BaseStateStore


class DefaultStateStore(BaseStateStore):
    """Готовый StateStore на дефолтных моделях utils."""

    def __init__(self):
        super().__init__(
            binding_model=SyncBinding,
            checkpoint_model=SyncCheckpoint,
            item_state_model=SyncItemState,
        )
