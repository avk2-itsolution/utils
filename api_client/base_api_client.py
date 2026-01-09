import logging
import time

import httpx
from tenacity import RetryCallState, Retrying

from .auth_strategy import AuthStrategy, NoAuthStrategy
from .dto.api_config import ApiConfig
from .dto.auth_state import AuthState
from .dto.credentials import Credentials
from .dto.dto import LogLevel
from .dto.http_transport import HttpTransport
from .dto.rate_limit_state import RateLimitState
from .dto.retry_policy import RetryPolicy

from typing import Any, Optional, Mapping

from .errors import ApiError, AuthError, RateLimitError, RetryableError


class BaseApiClient:
    """
    Базовый клиент:
    - httpx.Client внутри HttpTransport
    - retry через tenacity
    - опционально httpx-auth (через HttpTransport.auth)
    - динамическая авторизация через AuthStrategy
    """

    def __init__(
            self,
            config: ApiConfig,
            credentials: Credentials,
            retry_policy: RetryPolicy,
            *,
            auth_state: Optional[AuthState] = None,
            rate_limit_state: Optional[RateLimitState] = None,
            httpx_auth: Optional[Any] = None,  # объект из httpx-auth
            auth_strategy: Optional[AuthStrategy] = None,
    ) -> None:
        self.config = config
        self.credentials = credentials
        self.auth_state = auth_state or AuthState()
        self.retry_policy = retry_policy
        self.rate_limit_state = rate_limit_state
        self.transport = HttpTransport(config=config, auth=httpx_auth)

        self.auth_strategy = auth_strategy or NoAuthStrategy(self.credentials, self.auth_state)

        self.logger = logging.getLogger(self.__class__.__name__)
        self._configure_logger()

    def _configure_logger(self) -> None:
        if self.config.log_level == LogLevel.DEBUG:
            self.logger.setLevel(logging.DEBUG)
        elif self.config.log_level == LogLevel.INFO:
            self.logger.setLevel(logging.INFO)
        elif self.config.log_level == LogLevel.ERROR:
            self.logger.setLevel(logging.ERROR)
        else:
            self.logger.setLevel(logging.CRITICAL)

    def _build_retrying(self) -> Retrying:
        retrying = self.retry_policy.build_retrying()

        # для логирования попыток tenacity-хуком
        def before(retry_state: RetryCallState) -> None:
            if self.logger.isEnabledFor(logging.INFO) and retry_state.attempt_number > 1:
                self.logger.info("Retry attempt %s", retry_state.attempt_number)

        retrying.before = before
        return retrying

    def _request(
            self,
            method: str,
            path: str,
            *,
            query: Optional[Mapping[str, Any]] = None,
            json: Any = None,
            data: Any = None,
            files: Any = None,
            extra_headers: Optional[Mapping[str, str]] = None,
    ) -> httpx.Response:
        url = self._build_url(path)

        def send() -> httpx.Response:
            headers: dict[str, str] = {}
            if extra_headers:
                headers.update(extra_headers)

            self.auth_strategy.apply(headers)
            self._check_rate_limit()

            self.on_before_request(method, url, headers, query, json, data, files)

            start = time.perf_counter()
            resp = self.transport.request(
                method=method,
                url=url,
                headers=headers,
                params=query,
                json=json,
                data=data,
                files=files,
            )
            elapsed = time.perf_counter() - start

            self.on_after_response(resp, elapsed)

            if self._is_auth_error(resp):
                if self._handle_auth_error(resp):
                    raise RetryableError("Auth refreshed, retry", status_code=resp.status_code, response=resp)
                self._raise_auth_error(resp)

            if self.retry_policy.is_retry_status(resp.status_code):
                raise RetryableError(f"Retryable status {resp.status_code}", status_code=resp.status_code,
                                     response=resp)

            self._raise_for_status(resp)
            return resp

        retrying = self._build_retrying()
        return retrying.call(send)


    def _build_url(self, path: str) -> str:
        # httpx.Client уже знает base_url, поэтому:
        return path  # можно передавать относительный путь, абсолютный тоже пройдет как есть


    def _check_rate_limit(self) -> None:
        if not self.rate_limit_state:
            return
        if not self.rate_limit_state.can_request():
            raise RateLimitError("Rate limit exceeded")
        self.rate_limit_state.register_request()


    def _is_auth_error(self, resp: httpx.Response) -> bool:
        return resp.status_code in (401, 403)


    def _handle_auth_error(self, resp: httpx.Response) -> bool:
        if self.logger.isEnabledFor(logging.WARNING):
            self.logger.warning("Auth error %s on %s", resp.status_code, resp.url)
        return self.auth_strategy.handle_unauthorized(resp)


    def _raise_auth_error(self, resp: httpx.Response) -> None:
        raise AuthError(f"Auth error {resp.status_code}", status_code=resp.status_code, response=resp)


    def _raise_for_status(self, resp: httpx.Response) -> None:
        if 200 <= resp.status_code < 300:
            return
        msg = f"API error {resp.status_code}: {self._truncate_safe_text(resp)}"
        raise ApiError(msg, status_code=resp.status_code, response=resp)


"""
import httpx_auth

config = ApiConfig(base_url="https://api.example.com", default_headers={"User-Agent": "IS-Client/1.0"})
creds = Credentials(api_key="secret-key")
retry = RetryPolicy(max_attempts=3)

# пример: API key в заголовке через httpx-auth
api_key_auth = httpx_auth.APIKeyHeader("X-API-Key", creds.api_key)

client = BaseApiClient(
    config=config,
    credentials=creds,
    retry_policy=retry,
    httpx_auth=api_key_auth,  # статичная авторизация
    # динамическая авторизация через BearerTokenAuthStrategy подключается отдельным параметром
)

resp = client._request("GET", "/v1/resources")
"""
