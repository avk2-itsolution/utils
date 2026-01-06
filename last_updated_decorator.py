import functools
from django.utils.timezone import now
from django.utils.dateparse import parse_datetime

from integration_utils.its_utils.app_settings.models import KeyValue


def sync_with_last_updated(key: str | None = None):
    """
    Декоратор: пробрасывает last_updated как datetime,
    а после выполнения обновляет KeyValue на момент начала вызова.
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            kv_key = f"{func.__name__}{'_' + key if key else ''}"
            kv, _ = KeyValue.objects.get_or_create(
                key=kv_key,
                defaults={"value": "2025-01-01T00:00:00+03:00"}
            )
            started_at = now()
            # парсим строку в datetime
            last_updated = parse_datetime(kv.value)

            result = func(*args, last_updated=last_updated, **kwargs)

            kv.value = started_at.isoformat()
            kv.save(update_fields=["value"])

            return result

        return wrapper

    return decorator
