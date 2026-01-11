import typing
from dataclasses import replace, dataclass
from typing import Any, Mapping, Optional
from datetime import datetime


@dataclass(frozen=True)
class ExternalKey:  # стабильный ключ во внешней системе
    system: str
    key: str
