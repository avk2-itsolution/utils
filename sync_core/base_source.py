from abc import ABC, abstractmethod
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Generic, Iterable, Optional, Tuple, TypeVar

import requests

from utils.sync_core.dto import ExternalKey, Payload
from utils.sync_core.errors import TemporarySourceError, PermanentSourceError
from utils.sync_core.interfaces import Source

TSource = TypeVar("TSource")
TItems = Iterable[tuple[ExternalKey, Payload[TSource]]]


class CheckpointType(str, Enum):
    """Виды чекпоинтов для Source."""

    UPDATED_AT = "updated_at"      # datetime → iso
    MONOTONIC_ID = "monotonic_id"  # int/str int
    CURSOR = "cursor"              # строка/next_page_token
    NONE = "none"                  # снапшоты без чекпоинта


class BaseSource(Source[TSource], Generic[TSource], ABC):
    """Базовый Source с унифицированным парсингом/валидацией чекпоинтов."""

    _FALLBACK_DATETIME_FORMATS = (
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%d %H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%S.%f%z",
    )

    def __init__(
        self,
        *,
        checkpoint_type: CheckpointType = CheckpointType.UPDATED_AT,
        checkpoint_required: bool = True,
        checkpoint_parser: Optional[Callable[[str], Any]] = None,
        checkpoint_formatter: Optional[Callable[[Any], str]] = None,
    ):
        self.checkpoint_type = checkpoint_type
        self.checkpoint_required = checkpoint_required and checkpoint_type is not CheckpointType.NONE
        self._checkpoint_parser = checkpoint_parser
        self._checkpoint_formatter = checkpoint_formatter

    def fetch(self, since_token: Optional[str]) -> Tuple[TItems, Optional[str]]:
        if self.checkpoint_required and since_token is None:
            raise PermanentSourceError("checkpoint required")

        parsed_checkpoint = self._parse_checkpoint(since_token) if since_token is not None else None
        try:
            items, raw_checkpoint = self._fetch(parsed_checkpoint)
        except (requests.RequestException, ConnectionError, TimeoutError) as exc:
            raise TemporarySourceError(str(exc)) from exc

        formatted_checkpoint = self._format_checkpoint(raw_checkpoint)
        return items, formatted_checkpoint

    @abstractmethod
    def _fetch(self, parsed_checkpoint: Any) -> Tuple[TItems, Optional[Any]]:
        """
        :param parsed_checkpoint: чекпоинт, распарсенный согласно checkpoint_type
        :return: (items, raw_checkpoint) — чекпоинт можно вернуть в «сыром» виде (datetime/int/str/None),
                 BaseSource отформатирует и провалидирует его.
        """
        ...

    def paginate_eager(
        self,
        start_token: Optional[str],
        fetch_page: Callable[[Optional[str]], tuple[list, Optional[str]]],
    ) -> Tuple[list, Optional[str]]:
        """Обходит постраничный API: fetch_page(token) -> (items, next_token)."""
        items: list = []
        token = start_token
        last_token = start_token
        while True:
            page_items, token = fetch_page(token)
            items.extend(page_items)
            if token is None:
                break
            last_token = token
        return items, last_token

    def paginate_iter(
        self,
        start_token: Optional[str],
        fetch_page: Callable[[Optional[str]], tuple[list, Optional[str]]],
    ) -> Tuple[Iterable[tuple], Optional[str]]:
        """Ленивый обход постраничного API: отдаёт генератор пар и последний next_token."""
        last_token = start_token

        def _iter():
            nonlocal last_token
            token = start_token
            while True:
                page_items, token = fetch_page(token)
                for item in page_items:
                    yield item
                if token is None:
                    break
                last_token = token

        return _iter(), last_token

    def _parse_checkpoint(self, token: str) -> Any:
        """Парсинг входящего чекпоинта (строки из StateStore) в удобный тип для _fetch."""
        if self.checkpoint_type is CheckpointType.NONE:
            return None
        if self._checkpoint_parser:
            return self._checkpoint_parser(token)

        try:
            if self.checkpoint_type is CheckpointType.UPDATED_AT:
                return self._parse_datetime_token(token)
            if self.checkpoint_type is CheckpointType.MONOTONIC_ID:
                return self._parse_monotonic_token(token)
            if self.checkpoint_type is CheckpointType.CURSOR:
                return self._parse_cursor_token(token)
        except ValueError as exc:
            raise PermanentSourceError(f"invalid checkpoint '{token}': {exc}") from exc

        raise PermanentSourceError(f"unsupported checkpoint type: {self.checkpoint_type}")

    def _format_checkpoint(self, checkpoint: Optional[Any]) -> Optional[str]:
        """Форматирует и валидирует чекпоинт, возвращённый из _fetch, для записи в StateStore."""
        if checkpoint is None:
            if self.checkpoint_type is CheckpointType.NONE:
                return None
            return None  # отсутствие новых данных — просто не двигаем токен

        if self._checkpoint_formatter:
            return self._checkpoint_formatter(checkpoint)

        try:
            if self.checkpoint_type is CheckpointType.UPDATED_AT:
                dt = self._parse_datetime_value(checkpoint)
                return self._format_datetime(dt)
            if self.checkpoint_type is CheckpointType.MONOTONIC_ID:
                return self._format_monotonic(checkpoint)
            if self.checkpoint_type is CheckpointType.CURSOR:
                return self._format_cursor(checkpoint)
            if self.checkpoint_type is CheckpointType.NONE:
                raise ValueError("checkpoint type 'none' must not produce a checkpoint")
        except ValueError as exc:
            raise PermanentSourceError(f"invalid checkpoint value {checkpoint!r}: {exc}") from exc

        raise PermanentSourceError(f"unsupported checkpoint type: {self.checkpoint_type}")

    # --- helpers for checkpoint types ---

    def _parse_datetime_token(self, token: str) -> datetime:
        cleaned = token.strip()
        if cleaned.endswith("Z"):
            cleaned = f"{cleaned[:-1]}+00:00"
        try:
            return datetime.fromisoformat(cleaned)
        except ValueError:
            pass

        try:
            return datetime.fromtimestamp(float(cleaned), tz=timezone.utc)
        except ValueError:
            pass

        for fmt in self._FALLBACK_DATETIME_FORMATS:
            try:
                return datetime.strptime(cleaned, fmt).replace(tzinfo=timezone.utc)
            except ValueError:
                continue

        raise ValueError("cannot parse datetime")

    def _parse_datetime_value(self, value: Any) -> datetime:
        if isinstance(value, datetime):
            dt = value
        elif isinstance(value, (int, float)):
            dt = datetime.fromtimestamp(float(value), tz=timezone.utc)
        elif isinstance(value, str):
            dt = self._parse_datetime_token(value)
        else:
            raise ValueError("expected datetime/str/timestamp")

        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt

    def _format_datetime(self, dt: datetime) -> str:
        aware = dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
        return aware.astimezone(timezone.utc).isoformat()

    @staticmethod
    def _parse_monotonic_token(token: str) -> int:
        value = int(token)
        if value < 0:
            raise ValueError("monotonic id must be non-negative")
        return value

    @staticmethod
    def _format_monotonic(value: Any) -> str:
        int_value = int(value)
        if int_value < 0:
            raise ValueError("monotonic id must be non-negative")
        return str(int_value)

    @staticmethod
    def _parse_cursor_token(token: str) -> str:
        cleaned = token.strip()
        if not cleaned:
            raise ValueError("cursor cannot be empty")
        return cleaned

    @staticmethod
    def _format_cursor(value: Any) -> str:
        token = str(value).strip()
        if not token:
            raise ValueError("cursor cannot be empty")
        return token
