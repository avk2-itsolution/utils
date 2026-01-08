__all__ = [
    "BaseStateStore",
    "DefaultStateStore",
    "AbstractSyncBinding",
    "AbstractSyncCheckpoint",
    "AbstractSyncItemState",
    "SyncBinding",
    "SyncCheckpoint",
    "SyncItemState",
]


def __getattr__(name):
    if name == "BaseStateStore":
        from .stores.base import BaseStateStore
        return BaseStateStore
    if name == "DefaultStateStore":
        from .stores.default import DefaultStateStore
        return DefaultStateStore
    if name in {
        "AbstractSyncBinding",
        "AbstractSyncCheckpoint",
        "AbstractSyncItemState",
        "SyncBinding",
        "SyncCheckpoint",
        "SyncItemState",
    }:
        from .models import default
        return getattr(default, name)
    raise AttributeError(name)
