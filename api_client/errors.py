from abc import ABC, abstractmethod
from typing import Optional
import logging


class ApiError(Exception):
    def __init__(self, message: str, *, status_code: Optional[int] = None, response: Optional[httpx.Response] = None):
        super().__init__(message)
        self.status_code = status_code
        self.response = response


class RetryableError(ApiError):
    """Сигнал для tenacity: можно повторить запрос."""
    pass


class AuthError(ApiError):
    pass


class RateLimitError(ApiError):
    pass


class TemporaryApiError(ApiError):
    pass
