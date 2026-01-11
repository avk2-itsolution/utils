import typing
from dataclasses import replace
from typing import Any, Mapping, Optional
from datetime import datetime

from sync_utils.dataclass_compat import dataclass_compat as dataclass


@dataclass(frozen=True, slots=True)
class ExternalKey:  # стабильный ключ во внешней системе
    system: str
    key: str
