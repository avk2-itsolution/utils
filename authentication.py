from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

from integration_utils.bitrix24.bitrix_user_auth.authenticate_on_start_application import (
    authenticate_on_start_application,
)
from integration_utils.bitrix24.bitrix_user_auth.get_bitrix_user_token_from_header import (
    InvalidHeader,
    get_bitrix_user_token_from_header,
)


class BitrixMainAuthAuthentication(BaseAuthentication):
    """Аутентификация DRF через main_auth: сначала on_start, затем on_header."""

    def authenticate(self, request):
        raw_request = request._request
        self._authenticate_on_start(raw_request)
        self._authenticate_on_header(raw_request)

        bitrix_user_token = getattr(raw_request, "bitrix_user_token", None)
        if not bitrix_user_token:
            raise AuthenticationFailed("Не удалось выполнить авторизацию Bitrix24")

        bitrix_user = getattr(raw_request, "bitrix_user", None) or bitrix_user_token.user
        return bitrix_user, bitrix_user_token

    @staticmethod
    def _authenticate_on_start(request):
        has_on_start_payload = bool(request.POST.get("AUTH_ID") or request.POST.get("auth[access_token]"))
        if has_on_start_payload:
            authenticate_on_start_application(request=request)

    @staticmethod
    def _authenticate_on_header(request):
        try:
            get_bitrix_user_token_from_header(request=request)
        except InvalidHeader:
            pass  # выше по стеку обработка


# Совместимость с настройками DRF DEFAULT_AUTHENTICATION_CLASSES.
BitrixHeaderAuthentication = BitrixMainAuthAuthentication
