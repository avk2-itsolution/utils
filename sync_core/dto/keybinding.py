from dataclasses import dataclass

from . import ExternalKey, Binding


@dataclass(frozen=True)
class KeyBinding:
    key: ExternalKey
    binding: Binding
