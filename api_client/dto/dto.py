from __future__ import annotations

from enum import Enum, auto


class LogLevel(Enum):
    QUIET = auto()
    ERROR = auto()
    INFO = auto()
    DEBUG = auto()


class BackoffStrategy(Enum):
    FIXED = auto()
    EXPONENTIAL = auto()
