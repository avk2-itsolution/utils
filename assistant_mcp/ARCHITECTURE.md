# Assistant MCP: подключаемая архитектура

Практическая инструкция с готовыми `urls.py`, token adapter, `MCP_ACTIONS` и
local registry: [CONNECTING.md](CONNECTING.md).

`assistant_mcp` содержит переносимый MCP transport, общие read-only actions,
Bitrix REST sources, configuration parser и необязательный Django/DRF HTTP
adapter. Пакет не импортирует модели портала, Django settings, `get_token_app`
или конкретный логгер.

Проект создаёт пакет `mcp_actions_local` с явными `registry.build_server()` и
`urls.py`. В registry проект передаёт `McpLocalExtensions`: адаптер Bitrix
token/transport, доступные task sources, log source и зарегистрированные
локальные tools. `MCP_ACTIONS.tools.task_reader.source` выбирает встроенный
`bitrix_rest` или ключ source, явно зарегистрированный проектом (например,
`b24_db`). Неизвестный ключ является ошибкой конфигурации.

`build_urlpatterns(build_server)` сохраняет HTTP routes без импорта проекта из
utils. Для Django достаточно включить `mcp_actions_local.urls` под нужным
префиксом. Bearer token и allowed origins читаются из обычных project settings:
`MCP_TASKS_BEARER_TOKEN` и `MCP_TASKS_ALLOWED_ORIGINS`.
