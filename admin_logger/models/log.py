from django.contrib import admin
from django.db import models

from bitrix_robots.functions import debug_point_async
from integration_utils.bitrix24.models import BitrixUserToken


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

    class Admin(admin.ModelAdmin):
        ordering = ("-timestamp", "error_level")
        readonly_fields = ("timestamp",)
        list_display = ("timestamp", "error_place", "error_desc", "error_level")
        list_filter = ("error_level", "error_place",)
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
    def info(cls, error_desc: str, error_place: str = "mail_integration"):
        return cls.objects.create(
            error_place=error_place, error_desc=error_desc, error_level=cls.ErrorLevel.INFO)

    @classmethod
    def warning(cls, error_desc: str, error_place: str = "mail_integration", bitrix_notif_text: str = error_desc):
        debug_point_async(f'{error_place}: {error_desc}', with_tags=False)
        return cls.objects.create(
            error_place=error_place, error_desc=error_desc, error_level=cls.ErrorLevel.WARNING)

    @classmethod
    def error(cls, error_desc: str, error_place: str = "mail_integration", bitrix_notif_text: str = error_desc):
        debug_point_async(f'{error_place}: {error_desc}', with_tags=True)
        return cls.objects.create(
            error_place=error_place, error_desc=error_desc, error_level=cls.ErrorLevel.ERROR)

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