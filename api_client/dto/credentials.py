from sync_utils.dataclass_compat import dataclass_compat as dataclass
from typing import Optional


@dataclass(frozen=True, slots=True)
class Credentials:
    """Статичные данные авторизации (не access_token)."""
    api_key: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    refresh_token: Optional[str] = None

    def has_client_creds(self) -> bool:
        return bool(self.client_id and self.client_secret)

    def has_login_password(self) -> bool:
        return bool(self.username and self.password)
