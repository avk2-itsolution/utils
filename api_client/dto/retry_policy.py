from dataclasses import field
from enum import Enum, auto
from typing import Any, Optional, Sequence, Tuple, Type

from sync_utils.dataclass_compat import dataclass_compat as dataclass

import httpx
from tenacity import Retrying, stop_after_attempt, wait_fixed, wait_exponential, retry_if_exception_type


class BackoffStrategy(Enum):
    FIXED = auto()
    EXPONENTIAL = auto()


@dataclass(frozen=True, slots=True)
class RetryPolicy:
    max_attempts: int = 3
    backoff_strategy: BackoffStrategy = BackoffStrategy.EXPONENTIAL
    base_delay: float = 0.5
    max_delay: float = 10.0
    retry_statuses: Sequence[int] = field(default_factory=lambda: (500, 502, 503, 504))
    retry_exceptions: Tuple[Type[BaseException], ...] = (
        httpx.ConnectError,
        httpx.ReadTimeout,
        httpx.RemoteProtocolError,
    )

    def build_retrying(self) -> Retrying:
        if self.backoff_strategy == BackoffStrategy.FIXED:
            wait = wait_fixed(self.base_delay)
        else:
            wait = wait_exponential(multiplier=self.base_delay, max=self.max_delay)
        return Retrying(
            stop=stop_after_attempt(self.max_attempts),
            wait=wait,
            retry=retry_if_exception_type(self.retry_exceptions + (RetryableError,)),
            reraise=True,
        )

    def is_retry_status(self, status_code: int) -> bool:
        return status_code in self.retry_statuses
