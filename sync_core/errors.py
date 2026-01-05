class SyncError(Exception):
    """Базовая ошибка синхронизации."""


class SourceError(SyncError):
    """Ошибка на уровне источника (доступ, формат, протокол)."""


class MappingError(SyncError):
    """Ошибка маппинга/бизнес-правил."""


class TargetError(SyncError):
    """Ошибка при записи в приёмник (API/БД/валидатор)."""


class StateError(SyncError):
    """Ошибка состояния синка (биндинги, чекпоинты и т.п.)."""


class TemporaryError(SyncError):
    """Временная ошибка, которую можно/нужно ретраить."""


class PermanentError(SyncError):
    """Постоянная ошибка, ретраи бессмысленны."""


class TemporarySourceError(SourceError, TemporaryError):
    """Временная ошибка источника (сеть, 5xx и т.п.)."""


class PermanentSourceError(SourceError, PermanentError):
    """Постоянная ошибка источника (битый формат данных и т.п.)."""


class TemporaryMappingError(MappingError, TemporaryError):
    """Временная ошибка маппинга (например, временно недоступен справочник)."""


class PermanentMappingError(MappingError, PermanentError):
    """Постоянная бизнес-ошибка данных."""


class TemporaryTargetError(TargetError, TemporaryError):
    """Временная ошибка приёмника (таймауты, 5xx и т.п.)."""


class PermanentTargetError(TargetError, PermanentError):
    """Постоянная ошибка приёмника (валидация, 4xx)."""


class TemporaryStateError(StateError, TemporaryError):
    """Временная ошибка хранилища состояния."""


class PermanentStateError(StateError, PermanentError):
    """Постоянная ошибка хранилища состояния."""
