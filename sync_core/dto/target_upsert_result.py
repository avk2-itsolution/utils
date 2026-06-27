from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True, slots=True)
class TargetUpsertResult:
    """Результат upsert в target."""

    kind: Literal["completed", "deferred"]
    internal_id: str | None = None
    command_id: int | None = None

    def __post_init__(self) -> None:
        if self.kind == "completed":
            if self.internal_id is None:
                raise ValueError("completed target result requires internal_id")
            if self.command_id is not None:
                raise ValueError("completed target result must not contain command_id")
            return

        if self.kind == "deferred":
            if self.command_id is None:
                raise ValueError("deferred target result requires command_id")
            if self.internal_id is not None:
                raise ValueError("deferred target result must not contain internal_id")
            return

        raise ValueError(f"unsupported target result kind: {self.kind}")

    @classmethod
    def completed(cls, internal_id: str) -> "TargetUpsertResult":
        return cls(kind="completed", internal_id=internal_id)

    @classmethod
    def deferred(cls, command_id: int) -> "TargetUpsertResult":
        return cls(kind="deferred", command_id=command_id)

    @property
    def is_deferred(self) -> bool:
        return self.kind == "deferred"

    def get_internal_id(self) -> str:
        if self.internal_id is None:
            raise ValueError("deferred target result does not have internal_id")
        return self.internal_id
