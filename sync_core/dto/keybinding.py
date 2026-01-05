from dataclasses import dataclass

from utils.sync_core.dto import ExternalKey, Binding


@dataclass(frozen=True, slots=True)
class KeyBinding:
    key: ExternalKey
    binding: Binding
