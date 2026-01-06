from dataclasses import dataclass, field
from datetime import timedelta, datetime
from typing import Mapping, Tuple, Optional

from utils.api_client.dto.dto import LogLevel


@dataclass(slots=True)
class AuthState:
    """Динамическое состояние авторизации."""
    access_token: Optional[str] = None
    expires_at: Optional[datetime] = None
    refresh_required: bool = False

    def mark_for_refresh(self) -> None:
        self.refresh_required = True

    def set_token(self, token: str, lifetime: Optional[timedelta] = None) -> None:
        self.access_token = token
        self.refresh_required = False
        self.expires_at = datetime.utcnow() + lifetime if lifetime else None

    def is_expired(self, *, now: Optional[datetime] = None) -> bool:
        if self.refresh_required:
            return True
        if not self.access_token:
            return True
        if not self.expires_at:
            return False
        now = now or datetime.utcnow()
        return now >= self.expires_at
