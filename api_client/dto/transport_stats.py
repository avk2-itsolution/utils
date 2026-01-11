from dataclasses import field, dataclass
from statistics import mean
from typing import Any, Mapping, Optional

import httpx


@dataclass()
class TransportStats:
    total_requests: int = 0
    last_status_code: Optional[int] = None
    latencies: list[float] = field(default_factory=list)

    @property
    def avg_latency(self) -> Optional[float]:
        return mean(self.latencies) if self.latencies else None
