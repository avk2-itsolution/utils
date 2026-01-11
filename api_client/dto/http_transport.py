from __future__ import annotations

from dataclasses import field, dataclass
from typing import Any, Dict, Iterable, Mapping, Optional

import httpx

from .api_config import ApiConfig
from .transport_stats import TransportStats

@dataclass()
class HttpTransport:
    """
    Обёртка над httpx.Client.
    auth можно передать объектом из httpx-auth (например, APIKeyHeader, OAuth2, и т.п.).
    """
    config: ApiConfig
    auth: Optional[Any] = None  # сюда попадает любой httpx.Auth
    client: httpx.Client = field(init=False)
    stats: TransportStats = field(default_factory=TransportStats)

    def __post_init__(self) -> None:
        timeout = httpx.Timeout(
            self.config.read_timeout,
            connect=self.config.connect_timeout,
        )
        self.client = httpx.Client(
            base_url=self.config.base_url,
            timeout=timeout,
            verify=self.config.verify_ssl,
            headers=dict(self.config.default_headers),
            auth=self.auth,
        )

    def close(self) -> None:
        self.client.close()

    def request(
        self,
        method: str,
        url: str,
        *,
        headers: Optional[Mapping[str, str]] = None,
        params: Optional[Mapping[str, Any]] = None,
        json: Any = None,
        data: Any = None,
        files: Any = None,
    ) -> httpx.Response:
        import time
        merged_headers = dict(self.client.headers)
        if headers:
            merged_headers.update(headers)
        start = time.perf_counter()
        resp = self.client.request(
            method=method,
            url=url,
            params=params,
            json=json,
            data=data,
            files=files,
            headers=merged_headers,
        )
        elapsed = time.perf_counter() - start
        self.stats.total_requests += 1
        self.stats.last_status_code = resp.status_code
        self.stats.latencies.append(elapsed)
        return resp

