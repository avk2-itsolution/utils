# Подключение `assistant_mcp` в новый Django-проект

Это рабочая инструкция для проекта, который хочет получить read-only Bitrix MCP
без копирования `mcp_server.py`. В проекте остаются только token adapter,
несекретный config и actions, которые действительно зависят от его БД/портала.

## 1. Подключить URLs

Создать отслеживаемый Git пакет `mcp_actions_local` и в корневом `urls.py`
подключить его:

```python
from django.urls import include, path

urlpatterns += [
    path("mcp/", include("mcp_actions_local.urls")),
]
```

`mcp_actions_local/urls.py` всегда выглядит почти одинаково:

```python
from utils.assistant_mcp.django import build_urlpatterns
from .registry import build_server

app_name = "mcp_tasks"  # можно оставить для обратной совместимости reverse()
urlpatterns = build_urlpatterns(build_server)
```

Это создаёт следующие endpoints без нового ASGI/FastMCP service:

```text
POST /mcp/b24-tasks/              MCP JSON-RPC
GET  /mcp/tasks/<operation>/      legacy task REST reader
GET  /mcp/business-processes/<operation>/  legacy BP REST reader
GET  /mcp/, /mcp/tasks/, /mcp/business-processes/  manifests
```

## 2. Передать Bitrix token adapter

Framework не получает токен сам. Проект должен завернуть свой существующий
способ получения `BaseBitrixToken` в объект с двумя методами:

```python
# mcp_actions_local/adapters.py
from typing import Any, Mapping
from my_project.bitrix import get_token_app


class ProjectBitrixTransport:
    @property
    def token(self):
        return get_token_app()

    def call_api_method(self, method: str, fields: Mapping[str, Any]):
        return self.token.call_api_method(method, dict(fields))

    def call_list_method(self, method: str, *, fields: Mapping[str, Any], limit: int | None = None):
        return self.token.call_list_method(method, fields=dict(fields), limit=limit)
```

Token credentials остаются в привычных settings/env проекта. Не передавать
token в `MCP_ACTIONS`, не писать его в `mcp_actions_local` и не коммитить.

## 3. Указать settings

Для проекта **без** реплики `b24_db`:

```python
MCP_ACTIONS = {
    "server": {
        "name": "my-portal-readonly",
        "title": "My portal read-only data",
        "version": "1.0.0",
        "portal_domain": "my.bitrix24.ru",  # metadata, not secret
    },
    "tools": {
        "task_reader": {
            "enabled": True,
            "source": "bitrix_rest",
            "group_id": 42,  # optional task scope
        },
        "business_process_reader": {"enabled": True},
        "log_reader": {"enabled": False},
    },
    "local_actions": {},
}

MCP_TASKS_BEARER_TOKEN = env("MCP_TASKS_BEARER_TOKEN")
MCP_TASKS_ALLOWED_ORIGINS = ("https://assistant.example",)
```

`MCP_TASKS_BEARER_TOKEN` защищает MCP endpoint и legacy readers с данными
(`tasks/...`, `business-processes/...`). `MCP_TASKS_ALLOWED_ORIGINS` нужен
только для browser-origin запросов; запросы без `Origin` не блокируются.

## 4. Собрать server

Обычный REST-only проект:

```python
# mcp_actions_local/registry.py
from django.conf import settings
from utils.assistant_mcp import McpLocalExtensions, ProjectMcpConfig, ToolRegistry, build_mcp_server
from .adapters import ProjectBitrixTransport


def build_server():
    config = ProjectMcpConfig.from_settings(settings)
    local_tools = ToolRegistry()
    register_actions(local_tools, config)
    return build_mcp_server(
        config,
        McpLocalExtensions(
            token_provider=ProjectBitrixTransport,
            local_tools=tuple(local_tools),
        ),
    )


def register_actions(registry, config):
    pass  # explicit project-only actions go here
```

Так проект получает:

- `b24_task_read` с `source: bitrix_rest` и операцией `get_by_id`;
- `b24_bizproc_read` со всеми общими BP операциями;
- без `django_log_read`, потому что он выключен в config.

## Вариант с локальной БД задач

Если задача требует поиска по comments/full-text или нестандартным полям,
создать `B24DbTaskSource` в `mcp_actions_local` и зарегистрировать его:

```python
extensions = McpLocalExtensions(
    token_provider=ProjectBitrixTransport,
    task_sources={"b24_db": B24DbTaskSource(config.task_reader.group_id)},
    log_source=ProjectLogSource(),  # только если включён log_reader
    local_tools=tuple(local_tools),
)
```

Тогда в settings указать `"source": "b24_db"`. Имя внешнего tool остаётся
`b24_task_read`; меняются только доступные операции и источник ответа.
`bitrix_rest` встроен в framework, `b24_db` — только ключ локально переданного
source. Неправильный или незарегистрированный source вызывает configuration
error при старте, а не тихо переключается на другой источник.

## Добавление portal-specific tool

1. Создать Python-модуль в `mcp_actions_local`.
2. Положить portal ID/filters в `MCP_ACTIONS.local_actions["stable_key"]`.
3. В `register_actions()` явно добавить `McpTool` в `ToolRegistry`.
4. Не повторять имена `b24_task_read`, `b24_bizproc_read`, `django_log_read`.

Не использовать dynamic import из settings, autoload по папке или ignored Python:
набор tools должен воспроизводиться из Git на другом проекте и CI.

## После подключения

1. Перезапустить текущий Django process.
2. Вызвать `initialize`, затем `tools/list`.
3. Вызвать реальный `b24_bizproc_read` с `{"operation": "search_templates", "limit": 1}`.
4. Проверить `source: bitrix_rest` и точный `returned_count: 1`.

`limit` для BP соблюдается даже если Bitrix присылает первую страницу из 50
элементов. Текущее поле `total` равно количеству возвращённых элементов и не
является полным количеством данных на портале.

При изменении framework сначала коммитится и публикуется `utils`, затем проект
фиксирует новый SHA submodule. Иначе другой компьютер не сможет checkout
проектный commit.
