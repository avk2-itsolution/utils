from __future__ import annotations

from dataclasses import field
from datetime import datetime, timedelta
from typing import Any, Dict, Iterable, Mapping, MutableMapping, Optional, Sequence, Tuple, Type

from sync_utils.dataclass_compat import dataclass_compat as dataclass


@dataclass(slots=True)
class RateLimitState:
    """Простая модель лимитов за окно времени."""
    limit_per_window: int
    window_size: timedelta
    window_start: datetime
    used_in_window: int = 0

    def can_request(self, *, now: Optional[datetime] = None) -> bool:
        now = now or datetime.utcnow()
        self._maybe_roll_window(now)
        return self.used_in_window < self.limit_per_window

    def register_request(self, *, now: Optional[datetime] = None) -> None:
        now = now or datetime.utcnow()
        self._maybe_roll_window(now)
        self.used_in_window += 1

    def _maybe_roll_window(self, now: datetime) -> None:
        if now - self.window_start >= self.window_size:
            self.window_start = now
            self.used_in_window = 0
