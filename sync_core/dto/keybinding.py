from sync_utils.dataclass_compat import dataclass_compat as dataclass

from . import ExternalKey, Binding


@dataclass(frozen=True, slots=True)
class KeyBinding:
    key: ExternalKey
    binding: Binding
