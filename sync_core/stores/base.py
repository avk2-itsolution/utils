from typing import Iterable, Optional, Type

from django.db import models

from ..dto import ExternalKey, Binding, KeyBinding, SyncItemState, SyncItemStatus
from ..errors import StateError
from ..interfaces import StateStore


class BaseStateStore(StateStore):
    """Базовая реализация StateStore на Django-моделях."""

    def __init__(
        self,
        *,
        binding_model: Type[models.Model],
        checkpoint_model: Type[models.Model],
        item_state_model: Type[models.Model],
    ):
        self.binding_model = binding_model
        self.checkpoint_model = checkpoint_model
        self.item_state_model = item_state_model

    def get_checkpoint(self, stream: str) -> Optional[str]:
        row = self.checkpoint_model.objects.filter(stream=stream).only("token").first()
        return row.token if row else None

    def save_checkpoint(self, stream: str, token: str) -> None:
        self.checkpoint_model.objects.update_or_create(stream=stream, defaults={"token": token})

    def bind(self, key: ExternalKey, internal_id: str, version: Optional[str]) -> None:
        self.binding_model.objects.update_or_create(
            system=key.system,
            ext_key=key.key,
            defaults={"internal_id": internal_id, "version": version or ""},
        )

    def get_binding(self, key: ExternalKey) -> Optional[Binding]:
        row = (
            self.binding_model.objects.filter(system=key.system, ext_key=key.key)
            .only("internal_id", "version")
            .first()
        )
        if not row:
            return None
        return Binding(internal_id=row.internal_id, version=row.version or None)

    def iter_bindings(self, system: str) -> Iterable[KeyBinding]:
        qs = (
            self.binding_model.objects.filter(system=system)
            .only("ext_key", "internal_id", "version")
            .iterator()
        )
        for row in qs:
            yield KeyBinding(
                key=ExternalKey(system=system, key=row.ext_key),
                binding=Binding(internal_id=row.internal_id, version=row.version or None),
            )

    def validate_binding(self, key: ExternalKey, binding: Binding) -> None:
        if not binding.internal_id:
            raise StateError(f"empty internal_id for {key}")

    def get_item_state(self, key: ExternalKey) -> Optional[SyncItemState]:
        row = (
            self.item_state_model.objects.filter(system=key.system, ext_key=key.key)
            .only("version", "status", "attempts", "last_error")
            .first()
        )
        if not row:
            return None
        return SyncItemState(
            key=key,
            version=row.version or None,
            status=SyncItemStatus(row.status),
            attempts=row.attempts,
            last_error=row.last_error or None,
        )

    def save_item_state(self, state: SyncItemState) -> None:
        self.item_state_model.objects.update_or_create(
            system=state.key.system,
            ext_key=state.key.key,
            defaults={
                "version": state.version or "",
                "status": state.status.value,
                "attempts": state.attempts,
                "last_error": state.last_error or "",
            },
        )
