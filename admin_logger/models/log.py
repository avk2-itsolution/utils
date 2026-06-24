import functools
import traceback
from types import FunctionType
from typing import Any, Self

from django.contrib import admin
from django.db import models
from django_admin_filters import DateRange, DateRangePicker  # pip install django-admin-list-filters

from integration_utils.bitrix24.models import BitrixUserToken

from utils.cron_run_result import CronRunResult
from utils.functions1 import debug_point_async

USER_IDS_FOR_NOTIFICATION = []


class Log(models.Model):
    """Модель для логирования ошибок в админке

    имеет 3 уровня ошибок:

    Info: пометки, о которых хочется знать. Не отправляет сообщение в тг логгер.
    Warning: предупреждение. Отправляет сообщение в тг логгер, но не тегает.
    Error: ошибка. Отправляет сообщение в тг логгер, тегает.
    """
    class ErrorLevel(models.TextChoices):
        ERROR = 'error', 'error'
        WARNING = 'warning', 'warning'
        INFO = 'info', 'info'

    timestamp = models.DateTimeField("Время", auto_now_add=True)
    error_place = models.TextField("Где произошла ошибка")
    error_desc = models.TextField("Описание ошибки")
    error_level = models.TextField(verbose_name="Уровень ошибки", choices=ErrorLevel.choices)

    traceback = models.TextField("Traceback", blank=True, null=True)

    class Admin(admin.ModelAdmin):
        ordering = ("-timestamp", "error_level")
        readonly_fields = ("timestamp",)
        list_display = ("timestamp", "error_place", "error_desc", "error_level")
        list_filter = ("error_level", "error_place", ("timestamp", DateRangePicker))
        search_fields = ("error_desc",)  # поиск по тексту ошибки

        def get_search_results(self, request, queryset, search_term):
            term = search_term.strip()
            negate = False
            if term.startswith("!"):
                negate = True
                term = term[1:].strip()
            qs, use_distinct = super().get_search_results(request, queryset, term)
            if negate and term:
                qs = queryset.exclude(error_desc__icontains=term)
            return qs, use_distinct

    @classmethod
    def info(cls, error_desc: str, error_place: str = "mail_integration") -> Self:
        return cls.objects.create(
            error_place=error_place, error_desc=error_desc, error_level=cls.ErrorLevel.INFO)

    @classmethod
    def warning(cls, error_desc: str, error_place: str = "mail_integration", bitrix_notif_text: str = error_desc,
                traceback_text: str | None = None) -> Self:
        debug_point_async(f'{error_place}: {error_desc}', with_tags=False)
        return cls.objects.create(
            error_place=error_place, error_desc=error_desc, error_level=cls.ErrorLevel.WARNING)

    @classmethod
    def error(cls, error_desc: str, error_place: str = "mail_integration", bitrix_notif_text: str = error_desc,
              traceback_text: str | None = None) -> Self:
        debug_point_async(f'{error_place}: {error_desc}', with_tags=True)
        return cls.objects.create(
            error_place=error_place, error_desc=error_desc, error_level=cls.ErrorLevel.ERROR, traceback=traceback_text)

    @staticmethod
    def notify_bitrix(message: str):
        try:
            but = BitrixUserToken.get_admin_token()
            for user_id in USER_IDS_FOR_NOTIFICATION:
                but.call_api_method('im.notify.personal.add', {
                    'USER_ID': user_id,
                    'MESSAGE': message
                })
        except Exception as err:
            debug_point_async('Не удалось отправить уведомление об ошибке в Битрикс' + str(err), with_tags=True)

    @staticmethod
    def send_timeline_comment(entity_type: str, entity_id: int, comment: str):
        try:
            but = BitrixUserToken.get_admin_token()
            but.call_api_method('crm.timeline.comment.add', {'fields': {
            "ENTITY_ID": entity_id,
            "ENTITY_TYPE": entity_type,
            "COMMENT": comment,
            # "AUTHOR_ID": 'значение', ???????????
            }})
        except Exception as err:
            debug_point_async(f'entity_type: {entity_type}, entity_id: {entity_id} - Не удалось отправить сообщение об ошибке в таймлайн Битрикс' + str(err), with_tags=True)


    @classmethod
    def error_decorator(cls, error_return_value: Any = None,
                        error_comment: str | None = None,
                        log_place: str | None = None,
                        cron_result: bool = False) -> Any:
        """
        Декоратор для логирования ошибок на уровне error при любом исключении
        Место и описание ошибки определяются автоматически:
        error_place: <module>.<qualname>
        error_desc: repr(exc)
        При ошибке возвращает error_return_value как результат.
        При cron_result=True результат будет помещён в CronRunResult.
        """
        def inner(func: FunctionType):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except Exception as exc:
                    # Определение error_place
                    if log_place:
                        error_place = log_place
                    else:
                        error_place = f"{func.__module__}.{func.__qualname__}"

                    # Формирование error_desc
                    params_repr = f"args={args}, kwargs={kwargs}"
                    error_lines = [
                        f"Вызов функции {func.__qualname__} с параметрами {params_repr}.",
                        f"Возникла ошибка: {repr(exc)}"
                    ]
                    if error_comment:
                        error_lines.append(f"Комментарий: {error_comment}")

                    error_desc = "\n".join(error_lines)

                    traceback_text = traceback.format_exc()

                    cls.error(
                        error_desc=error_desc,
                        error_place=error_place,
                        traceback_text=traceback_text
                    )

                    if cron_result:
                        return CronRunResult.failure(error=error_desc, result=error_return_value)
                    return error_return_value

            return wrapper

        return inner

    @classmethod
    def info_decorator(cls):
        """Декоратор для логирования вызовов функций и ее входных параметров"""
        def inner(func: FunctionType):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                # Определение error_place
                error_place = f"{func.__module__}.{func.__qualname__}"

                # Формирование error_desc
                params_repr = f"{args=}, {kwargs=}"
                error_lines = [
                    f"Вызов функции {func.__qualname__} с параметрами {params_repr}.",
                ]

                error_desc = "\n".join(error_lines)

                cls.info(
                    error_desc=error_desc,
                    error_place=error_place,
                )
                return func(*args, **kwargs)

            return wrapper

        return inner
