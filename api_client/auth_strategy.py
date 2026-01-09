from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Optional
import logging
import time

import httpx
import requests
from requests import Response

from .dto.auth_state import AuthState
from .dto.credentials import Credentials


# предполагаем, что эти классы уже есть
# from .base_entities import ApiConfig, Credentials, AuthState, RetryPolicy, RateLimitState, HttpTransport, LogLevel


class ApiError(Exception):
    def __init__(self, message: str, *, status_code: Optional[int] = None, response: Optional[httpx.Response] = None):
        super().__init__(message)
        self.status_code = status_code
        self.response = response


class AuthError(ApiError): pass
class RateLimitError(ApiError): pass
class TemporaryApiError(ApiError): pass


from abc import ABC, abstractmethod


class AuthStrategy(ABC):
    """
    Для динамических схем авторизации (access_token в AuthState).
    Статические схемы типа api-key можно отдать на httpx-auth через HttpTransport.auth.
    """
    def __init__(self, credentials: Credentials, auth_state: AuthState):
        self.credentials = credentials
        self.auth_state = auth_state

    @abstractmethod
    def apply(self, headers: dict[str, str]) -> None:
        raise NotImplementedError

    def handle_unauthorized(self, response: httpx.Response) -> bool:
        return False



class NoAuthStrategy(AuthStrategy):
    def apply(self, headers: dict[str, str]) -> None:
        return



class BearerTokenAuthStrategy(AuthStrategy):
    """Простейший вариант, когда токен лежит в AuthState."""
    def apply(self, headers: dict[str, str]) -> None:
        if not self.auth_state.access_token:
            return
        headers.setdefault("Authorization", f"Bearer {self.auth_state.access_token}")



