from enum import Enum


class SyncItemStatus(str, Enum):
    PENDING = "pending"       # ещё не пробовали
    SUCCESS = "success"       # успешно синхронизировано
    TEMP_ERROR = "temp_error" # временная ошибка, можно ретраить
    PERM_ERROR = "perm_error" # постоянная ошибка, больше не трогаем


