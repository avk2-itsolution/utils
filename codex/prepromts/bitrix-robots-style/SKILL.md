---
name: bitrix-robots-style
description: "Use when creating, modifying, reviewing, or debugging Bitrix24 business-process robot actions in Django projects based on `integration_utils.bitrix_robots.models.BaseRobot`, including `CODE`, `NAME`, `PROPERTIES`, `RETURN_PROPERTIES`, `VALIDATE_PROPS`, `PROCESS_ON_REQUEST`, `process()`, install/uninstall views, handler URLs, admin, migrations, cron processing, and BaseRobot result contracts."
---

# Как создавать роботов

Робот здесь - это действие бизнес-процесса Bitrix24, оформленное Django-моделью, наследованной от `integration_utils.bitrix_robots.models.BaseRobot`.

## Быстрый порядок

1. Найди соседние примеры:

```powershell
rg -n "BaseRobot|install_or_update|process_robot_requests" -g "*.py"
```

2. Выбери место по владельцу логики:
   - `app/models/robots/<name>.py` - предпочтительно для новых app-local роботов.
   - `bitrix_robots/<robot_app>/...` - только если робот уже живёт в старом отдельном robot-app стиле.
3. Опиши модель: `CODE`, `NAME`, `PROPERTIES`, `RETURN_PROPERTIES`, `process()`.
4. Добавь `handler` в `urls.py` через `Robot.as_view()`.
5. Добавь install/uninstall views через `install_or_update()` и `uninstall()`.
6. Импортируй модель в `models/__init__.py`, если app использует такой паттерн.
7. Добавь admin: `auto_register("app")` или локальный `class Admin`.
8. Сделай миграцию для новой модели.
9. Для долгих роботов включи `PROCESS_ON_REQUEST = False` и добавь cron на `process_robot_requests(Robot)`.
10. Проверь точечно: import/compile, migrations check, diff, кодировку.

## Что найдено в этом проекте

Опорный пример библиотеки: `integration_utils/bitrix_robots/example_robot/models/example_robot.py`.

Старые отдельные robot-apps: `AccessGetClientRobot`, `DocumentRobot`, `FingradGetRassrochkaRobot`, `PmAddUserRobot`, `PmGetSpecsRobot`, `PmGetUserRobot`.

App-local роботы:

- `pmanager`: `CreatePMLeadRobot`, `DetachPartnerAndProjectRobot`, `GetContractDataRobot`, `GetCustomerByPhoneRobot`, `LeadVerificationRobot`, `ProjectVerificationRobot`, `SendVerifyCustomerRobot`.
- `pyrus_integration`: `PyrusTaskAddRobot`, `PyrusTaskAddKitchenRobot`, `PyrusTaskAddOrderIssuesRobot`, `PyrusTaskAddRobotStatusChange`, `PyrusTaskAddWardrobeRobot`, `PyrusTaskAddVirtualShowroomRobot`, `PyrusTaskDeleteRobot`, `PyrusParentContractAttachRobot`.
- Остальные интеграции: `BitrixIvideonSyncRobot`, `LeadDistributionRobot`, `PolygonRobot`.

`check_system/classes/robot_health_check.py` - не робот, а мониторинг свежих записей BaseRobot.

## Контракт BaseRobot

`BaseRobot.as_view()`:

- читает POST через `get_params_from_sources`;
- проверяет Bitrix auth в `verify_event()`;
- создаёт запись модели с `params`, `token`, `event_token`;
- если `PROCESS_ON_REQUEST = True`, сразу вызывает `start_process()`;
- возвращает HTTP `ok`, если запрос принят.

`start_process()`:

- ставит `started = timezone.now()`;
- при `VALIDATE_PROPS = True` вызывает `validate_props()`;
- вызывает `process()`;
- сохраняет `result`, `is_success`, `finished`;
- если БП ждёт результат, отправляет `bizproc.event.send` через `send_result()`.

Поэтому обычно в `process()` нужно вернуть dict, а не вызывать `bizproc.event.send` вручную. Прямой `event.send` допустим только если сохраняешь уже существующее legacy-поведение.

## Шаблон модели

```python
from django.contrib import admin

from integration_utils.bitrix_robots.models import BaseRobot
from utils.types import RobotProcessResult


class FooRobot(BaseRobot):
    CODE = "foo_robot"
    NAME = "Короткое имя действия БП"
    VALIDATE_PROPS = True

    PROPERTIES = {
        "lead_id": {
            "Name": {"ru": "ID Лида"},
            "Type": "int",
            "Required": "Y",
        },
    }

    RETURN_PROPERTIES = {
        "ok": {"Name": {"ru": "ok"}, "Type": "bool", "Required": "Y"},
        "result": {"Name": {"ru": "result"}, "Type": "string", "Required": "N"},
        "error": {"Name": {"ru": "error"}, "Type": "string", "Required": "N"},
    }

    class Admin(admin.ModelAdmin):
        list_display = (*BaseRobot.Admin.list_display, "result")
        list_display_links = list_display

    def process(self) -> RobotProcessResult:
        lead_id: int = self.props["lead_id"]
        # Вызови domain/service-код здесь.
        return {"ok": True, "result": str(lead_id)}
```

Если `RobotProcessResult` в проекте не подходит или не импортируется, используй `dict`.

## PROPERTIES

Описывай только реальные входы БП.

Типы, которые уже используются и валидируются базой:

- `int`
- `bool`
- `string`
- `text`

Если включаешь `VALIDATE_PROPS = True`, BaseRobot нормализует одиночные простые props. Не ставь `Type: int`, если Bitrix фактически присылает строку вида `DYNAMIC_170_123` или `LEAD_123`; используй `string` и явно распарси.

Для множественных значений используй `Multiple: "Y"` и проверь, как `self.props[name]` приходит в соседних роботах.

Не читай одно значение из нескольких speculative ключей. Если формат неясен, сначала найди реальный POST/соседний пример.

## RETURN_PROPERTIES

Почти всегда добавляй:

```python
RETURN_PROPERTIES = {
    "ok": {"Name": {"ru": "ok"}, "Type": "bool", "Required": "Y"},
    "error": {"Name": {"ru": "error"}, "Type": "string", "Required": "N"},
}
```

Если БП должен получить данные, добавь явные поля: `result`, `contact_id`, `pm_customer_id`, `verified`, `dateCompletion` и т.п.

`process()` должен возвращать ключи, которые объявлены в `RETURN_PROPERTIES`. Boolean в результате BaseRobot преобразует в `Y`/`N` при отправке в БП.

## process()

Держи `process()` транспортным слоем:

- прочитать и проверить `self.props`;
- получить начальные объекты;
- вызвать domain/service/use-case;
- вернуть dict результата;
- преобразовать ожидаемые ошибки в понятный `{"ok": False, "error": message}`.

Не держи в роботе длинный сценарий, если есть предметный service. Хороший пример направления - `LeadDistributionRobot`: модель только читает `lead_id` и вызывает `LeadDistributionService`.

Для Bitrix token используй имя `but`:

```python
but = get_token_app()
```

или работай с `self.token`, если действие должно выполняться от пользователя/портала, приславшего событие.

Для времени в новом коде используй `django.utils.timezone`, не `datetime.datetime.now()`.

Не путай:

- `self.id` - id локальной записи робота;
- `self.props["..."]` - входные параметры БП;
- `self.params["document_id[2]"]` - служебные данные Bitrix, если они не объявлены в `PROPERTIES`.

## Ошибки

Лови известные ошибки интеграции раньше общего `Exception`: например `PMNotFoundError`, `PMException`.

Для бизнес-ошибок возвращай понятный результат:

```python
return {"ok": False, "error": message}
```

Если ошибка должна попасть в таймлайн или лог, используй существующий `Log`-паттерн соседнего app.

Не копируй старые анти-паттерны:

- bare `except`;
- `pass` при ошибке загрузки файла;
- молчаливые fallback-цепочки;
- ручной `bizproc.event.send` при обычном result flow;
- `self.id` вместо бизнес-id из props.

## Долгие роботы

Если робот делает внешние API, много DB/Bitrix операций или может выполняться дольше HTTP-ответа, ставь:

```python
PROCESS_ON_REQUEST = False
```

и добавляй cron:

```python
from admin_logger.models import Log
from integration_utils.bitrix_robots.cron import process_robot_requests
from its_utils.app_cron.cron_run_result import CronRunResult


@Log.error_decorator(cron_result=True)
def process_foo_robots():
    from app.models.robots.foo_robot import FooRobot
    return CronRunResult.success(process_robot_requests(FooRobot))
```

Если робот временно не готов к обработке, можно использовать `DelayProcess`: BaseRobot сбросит `started`, и cron сможет взять запись позже.

## URLs и install/uninstall

`urls.py`:

```python
from django.urls import path

from app.models.robots.foo_robot import FooRobot
from app.views import foo_robot_install, foo_robot_uninstall

app_name = "app"

urlpatterns = [
    path("foo_robot_install/", foo_robot_install, name="foo_robot_install"),
    path("foo_robot_uninstall/", foo_robot_uninstall, name="foo_robot_uninstall"),
    path("foo_robot_handler/", FooRobot.as_view(), name="foo_robot_handler"),
]
```

Install view:

```python
from django.http import HttpResponse

from app.models.robots.foo_robot import FooRobot
from integration_utils.bitrix24.bitrix_user_auth.main_auth import main_auth


@main_auth(on_cookies=True)
def foo_robot_install(request):
    try:
        FooRobot.install_or_update("app:foo_robot_handler", request.bitrix_user_token)
    except Exception as exc:
        return HttpResponse(str(exc))

    return HttpResponse("ok")
```

Uninstall view:

```python
@main_auth(on_cookies=True)
def foo_robot_uninstall(request):
    try:
        FooRobot.uninstall(request.bitrix_user_token)
    except Exception as exc:
        return HttpResponse(str(exc))

    return HttpResponse("ok")
```

`install_or_update()` вызывает write REST методы `bizproc.robot.add/update`, `uninstall()` вызывает `bizproc.robot.delete`. Не запускай их против production/read-only портала в диагностических задачах.

## Регистрация в Django

Для новой модели проверь:

- app есть в `INSTALLED_APPS`;
- app urls подключены в корневой `urls.py`;
- модель импортируется в `models/__init__.py`, если app так устроен;
- создана миграция;
- admin подключён через `auto_register("app")` или `class Admin`.

В admin для расширения списка полей предпочитай tuple style:

```python
list_display = (*BaseRobot.Admin.list_display, "result")
```

## Bitrix24 REST

Если робот использует новые методы, поля, события, payload или response shape Bitrix24, сначала проверяй документацию через `bitrix-mcp-rest`.

Не придумывай:

- имя REST метода;
- форму `params`;
- имена `fields`;
- структуру ответа;
- формат события БП.

## Проверка перед завершением

Минимум:

```powershell
py -3 -m py_compile path\to\changed_file.py
git diff --check
```

Для новой модели:

```powershell
py -3 manage.py makemigrations app_name --check --dry-run
```

Если startup проекта недоступен из-за окружения, явно напиши это и проверь хотя бы `py_compile`, `rg`, `git diff --check`.

Перед финалом проверь, что русский текст в diff читаемый и нет mojibake.

## Чеклист

- Наследуется от `BaseRobot`.
- `CODE` уникален и стабилен.
- `NAME` понятен пользователю БП.
- `PROPERTIES` описывают реальные входы.
- `RETURN_PROPERTIES` совпадают с результатом `process()`.
- `VALIDATE_PROPS = True`, если входы простые и формат соответствует типам.
- `process()` читает `self.props`, не `self.id`.
- Длинная работа вынесена в cron через `PROCESS_ON_REQUEST = False`.
- Handler, install, uninstall подключены в `urls.py`.
- Install использует точный namespace: `app_name:handler_name`.
- Модель импортируется для миграций/admin.
- Для новых Bitrix REST вызовов проверена документация.
- Проверки запущены или честно указано, почему не запущены.
