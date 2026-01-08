from utils.sync_core.base_state_store import BaseStateStore
from utils.sync_core.default_models import SyncBinding, SyncCheckpoint, SyncItemState


class DefaultStateStore(BaseStateStore):
    """Готовый StateStore на дефолтных моделях utils."""

    def __init__(self):
        super().__init__(
            binding_model=SyncBinding,
            checkpoint_model=SyncCheckpoint,
            item_state_model=SyncItemState,
        )
