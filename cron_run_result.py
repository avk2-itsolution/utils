from dataclasses import dataclass
from typing import Any, Self


@dataclass(frozen=True, slots=True)
class CronRunResult:
    """
    Результат выполнения крона для проверки в check_system.
    Ожидается, что все кроны будут возвращать CronRunResult, если они не упали.
    """
    ok: bool
    result: Any = None
    error: str | None = None

    @classmethod
    def success(cls, result: Any = None) -> Self:
        return cls(ok=True, result=result, error=None)

    @classmethod
    def failure(cls, error: str, result: Any = None) -> Self:
        error_text: str = repr(error) if error is not None else "unknown error"
        return cls(ok=False, result=result, error=error_text)

    @classmethod
    def from_exception(cls, exc: Exception) -> Self:
        error_text = repr(exc)
        return cls(ok=False, result=None, error=error_text)

    def __str__(self) -> str:
        return repr(self)

    @classmethod
    def from_str(cls, text: str) -> Self:
        """
        Восстанавливает CronRunResult из repr().
        """
        value = eval(text, {"CronRunResult": cls})

        if not isinstance(value, cls):
            raise TypeError("repr does not contain CronRunResult")

        return value
