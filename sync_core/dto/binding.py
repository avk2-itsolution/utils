from sync_utils.dataclass_compat import dataclass_compat as dataclass
from typing import Optional

from . import Payload


@dataclass(frozen=True, slots=True)
class Binding:
    """Связка внешней сущности с внутренней: ID + версия."""
    internal_id: str
    version: Optional[str] = None  # e.g. etag/updated_at/hash

    def is_up_to_date_for(self, payload: Payload) -> bool:
        """Версия внешних данных уже синхронизирована."""
        return self.version is not None and self.version == payload.version

