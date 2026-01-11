from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import typing
from typing import Any, Optional, Generic, TypeVar, Union

TSource = TypeVar("TSource")
SelfPayload = TypeVar("SelfPayload", bound="Payload")
VersionValue = Union[datetime, str, int, float]


@dataclass(frozen=True)
class Payload(Generic[TSource]):
    """Нормализованные данные из источника."""
    data: TSource
    version: Optional[str] = None  # etag/updated_at/hash

    _FALLBACK_DATETIME_FORMATS = (
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%d %H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%S.%f%z",
    )

    @classmethod
    def with_version_from_datetime(cls, data: TSource, dt: VersionValue) -> SelfPayload:
        """Фабрика Payload с версией, рассчитанной из datetime/ts/строки."""
        version = cls.version_from_datetime(dt)
        return cls(data=data, version=version)

    @classmethod
    def with_version_from_monotonic(cls, data: TSource, value: VersionValue) -> SelfPayload:
        """Фабрика Payload с версией, рассчитанной из монотонного id."""
        version = cls.version_from_monotonic(value)
        return cls(data=data, version=version)

    @classmethod
    def with_version_from_hash(cls, data: TSource) -> SelfPayload:
        """Фабрика Payload с версией, рассчитанной по sha256 от данных."""
        version = cls.version_from_hash(data)
        return cls(data=data, version=version)

    @staticmethod
    def version_from_datetime(value: VersionValue) -> str:
        """Форматирует дату/время (str/datetime/timestamp) в ISO-строку под Payload.version."""
        dt = Payload._parse_datetime_value(value)
        return Payload._format_datetime(dt)

    @staticmethod
    def version_from_monotonic(value: VersionValue) -> str:
        """Форматирует монотонный id в строку версии (проверяет на неотрицательное)."""
        int_value = int(value)
        if int_value < 0:
            raise ValueError("monotonic id must be non-negative")
        return str(int_value)

    @staticmethod
    def version_from_hash(payload: Any) -> str:
        """Вычисляет sha256 от JSON-представления payload для версионирования без updated_at."""
        try:
            dump = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        except (TypeError, ValueError) as exc:
            raise ValueError(f"cannot hash payload: {exc}") from exc
        return hashlib.sha256(dump.encode("utf-8")).hexdigest()

    @staticmethod
    def _parse_datetime_value(value: VersionValue) -> datetime:
        if isinstance(value, datetime):
            dt = value
        elif isinstance(value, (int, float)):
            dt = datetime.fromtimestamp(float(value), tz=timezone.utc)
        elif isinstance(value, str):
            dt = Payload._parse_datetime_token(value)
        else:
            raise ValueError("expected datetime/str/timestamp")

        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt

    @staticmethod
    def _parse_datetime_token(token: str) -> datetime:
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

        for fmt in Payload._FALLBACK_DATETIME_FORMATS:
            try:
                return datetime.strptime(cleaned, fmt).replace(tzinfo=timezone.utc)
            except ValueError:
                continue

        raise ValueError("cannot parse datetime")

    @staticmethod
    def _format_datetime(dt: datetime) -> str:
        aware = dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
        return aware.astimezone(timezone.utc).isoformat()
