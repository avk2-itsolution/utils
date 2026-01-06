import functools
import re
import threading
from types import FunctionType
from urllib.parse import unquote
import sys
import traceback
import requests
from typing import Text, Any

from django.conf import settings


REGEX_EMAIL = "([A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+)"
ASSIGN_USER = 2464


USERNAMES = "@avk_its\n\n"


def debug_point_async(message: Text, with_tags: bool = True, with_traceback: bool = True):
    tb_text: str | None = None
    if with_traceback and sys.exc_info()[0] is not None:
        tb_text = traceback.format_exc()

    thread = threading.Thread(
        target=debug_point,
        args=(message, with_tags, tb_text),
    )
    thread.start()


def debug_point(message: Text, with_tags: bool, tb_text: str | None = None):
    token = settings.DEBUG_BOT_TOKEN
    chat_id = settings.DEBUG_CHAT_ID

    if with_tags:
        message = f"{USERNAMES}{message}"

    if tb_text:
        message += f"\n\n{tb_text}"

    # Разбиваем на куски по 4096 символов
    chunk: str = ""
    for line in message.split("\n"):
        if len(chunk) + len(line) + 1 < 4096:
            chunk += "\n" + line
        else:
            requests.post(f"https://api.telegram.org/bot{token}/sendMessage", data={"chat_id": chat_id, "text": chunk})
            chunk = "\n" + line

    if chunk.strip():
        requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            data={"chat_id": chat_id, "text": chunk},
        )

def log_errors(message: Text, error_return_value: Any):
    """
    Декоратор для логирования ошибок
    Оборачивает функцию в широкий try-except, в котором при отлове любого исключения
    отправляется лог в телеграм-чат, и возвразается значение error_return_value
    Пример:

    @log_errors("Ошибка при сохранении запроса: ", error_return_value=HttpResponseServerError("ошибка при сохранении запроса"))
    """

    def inner(func: FunctionType):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                response = func(*args, **kwargs)
            except Exception as exc:
                debug_point_async(message + str(exc), with_tags=True)
                return error_return_value
            else:
                return response

        return wrapper

    return inner
