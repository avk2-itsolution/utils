from dataclasses import dataclass
from typing import Any, Mapping, Generic, TypeVar

TTarget = TypeVar("TTarget")  # что нужен Target'у


@dataclass
class Projection(Generic[TTarget]):
    """Что писать в приёмник."""
    kind: str
    data: TTarget  # вместо dict fields