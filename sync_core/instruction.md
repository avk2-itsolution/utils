# Руководство по использованию `sync_core` для односторонней синхронизации

## 1. Проверить, что задача вообще подходит под `sync_core`

- Односторонняя синхронизация (A → B).
- Есть стабильный внешний идентификатор (ID или составной ключ).
- Можно как-то определить, изменилась запись или нет:
  - `updated_at`,
  - hash,
  - версия,
  - снапшот.
- Удаления либо не нужны, либо их можно вычислить (снапшот + `iter_bindings`).

## 2. Продумать ключи и версии

- Определить `ExternalKey(system, key)` для каждой сущности:
  - что будет в `system`,
  - что будет в `key`.
- Определить, чем будет `Payload.version`:
  - `updated_at`,
  - hash,
  - ревизия.
- Решить, нужно ли `Target.delete` и `StateStore.iter_bindings` (снапшоты и чистка хвостов).

## 3. Спроектировать чекпоинты (`StateStore.get/save_checkpoint`)

Выбрать тип чекпоинта:

- `updated_at` (ISO), если есть поле времени;
- монотонный ID, если есть возрастающий ID;
- `cursor` / `next_page_token`, если даёт API;
- `None` + снапшоты, если ничего нет.

Решить, как этот токен будет использоваться в `Source.fetch`.

## 4. Реализовать `Source`

- `fetch(since_token)` получает данные из A и выдаёт `(ExternalKey, Payload)`.
- `validate(key, payload)` проверяет «сырьё» (есть обязательные поля, типы, формат) и кидает `SourceError` при проблемах.
- В снапшот-сценарии `since_token` может игнорироваться.

## 5. Спроектировать доменные объекты (желательно)

- Для основной сущности (`Task`, `Order` и т.п.) сделать `dataclass` с фабрикой `from_payload`.
- В `from_payload` выполнять бизнес-валидацию и кидать `MappingError` при некорректных данных.

## 6. Реализовать `Mapper`

- `validate(key, payload)` вызывает доменную фабрику и проверяет бизнес-правила.
- `map(key, payload)` строит `Projection(kind, fields)` в терминах системы B.
- Не ходит сам в сеть B, максимум читает справочники/кэш.

## 7. Реализовать `Target`

- `validate(key, projection)` проверяет, что `kind` и `fields` корректны для B, кидает `TargetError`.
- `upsert(key, projection)` делает `create/update` в B, возвращает `internal_id`.
- При необходимости реализовать `delete(key, binding)` для удалений/архивации.

## 8. Реализовать `StateStore`

- Django-модели для биндингов и чекпоинтов.
- `bind` / `get_binding` / `iter_bindings` — в одной общей таблице (`system` + `ext_key`).
- `validate_binding` проверяет консистентность (например, пустой `internal_id` → `StateError`).

## 9. Реализовать `SyncLogger`

- Логирование `created` / `updated` / `skipped` / `deleted` / `error`
  - в Django-логгер,
  - или в свою модель.

## 10. Собрать `SyncJob` под конкретный поток

- Определить `stream` (человекочитающая строка, например `"A_tasks->B_tasks"`).
- Создать экземпляры:
  - `Source`,
  - `Mapper`,
  - `Target`,
  - `StateStore`,
  - `SyncLogger`.
- Вызвать `job.run()` из management-команды или cron-функции.

## 11. Покрыть минимум тестами

Юнит-тесты для:

- `Source.fetch` — нормальный и битый ответ.
- Доменной фабрики и `Mapper`.
- `Target.upsert` / `Target.delete` с моканым клиентом B.
- `SyncJob.run` с фиктивными `StateStore` и `Source`, чтобы проверить:
  - `created`,
  - `updated`,
  - `skipped`,
  - `failed`.
