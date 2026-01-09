from dataclasses import dataclass, field
from typing import Mapping, Tuple

from .dto import LogLevel


@dataclass(frozen=True, slots=True)
class ApiConfig:
    """Базовые настройки клиента API."""
    base_url: str
    connect_timeout: float = 5.0
    read_timeout: float = 30.0
    default_headers: Mapping[str, str] = field(default_factory=dict)
    verify_ssl: bool = True
    log_level: LogLevel = LogLevel.ERROR

    @property
    def timeout(self) -> Tuple[float, float]:
        return self.connect_timeout, self.read_timeout
