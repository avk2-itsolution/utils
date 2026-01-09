from ..models import SyncBinding, SyncCheckpoint, SyncItemState
from .base import BaseStateStore


class DefaultStateStore(BaseStateStore):
    """Готовый StateStore на дефолтных моделях utils."""

    def __init__(self):
        super().__init__(
            binding_model=SyncBinding,
            checkpoint_model=SyncCheckpoint,
            item_state_model=SyncItemState,
        )
