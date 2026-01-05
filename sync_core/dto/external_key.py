import typing
from dataclasses import dataclass, replace
from typing import Any, Mapping, Optional
from datetime import datetime


@dataclass(frozen=True, slots=True)
class ExternalKey:  # стабильный ключ во внешней системе
    system: str
    key: str
