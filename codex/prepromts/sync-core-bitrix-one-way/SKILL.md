---
name: sync-core-bitrix-one-way
description: "Build one-way Django syncs on top of `utils.sync_core` from external systems into Bitrix24, including paginated `BaseSource`, normalized `Payload`, explicit `Projection`, pure `Mapper`, deferred `TargetUpsertResult`, and batched Bitrix writes through `utils.bitrix_batch`. Use when Codex needs to replace procedural transfer functions with `sync_core`, especially for large streams, incremental versioned sync, or cron-driven batch writes into Bitrix dynamic items."
---

# sync_core + Bitrix24

Проектируй одностороннюю синхронизацию как цепочку:

`Source -> Payload -> Mapper -> Projection -> Target -> StateStore`

Думай не про один procedural-скрипт, а про стабильный поток синхронизации, который можно безопасно гонять повторно.

## Базовые правила

- Сначала описывай предметную модель синка: какой `ExternalKey`, какая версия, какие поля реально пишутся в target.
- Потом раскладывай код по слоям `payload.py`, `projection.py`, `source.py`, `mapper.py`, `target.py`.
- Делай минимальную архитектуру. Для такого синка обычно достаточно:
  - dataclass payload
  - dataclass projection
  - source
  - mapper
  - target
  - callback завершения deferred-команды
- Не плодить дополнительные coordinator/service/orchestrator классы, если они не упрощают код очевидно.
- Не прятать ошибки через `pass`, `return None` и неясные fallback-цепочки.
- Использовать имя `but` для `BitrixUserToken`. Не вводить альтернативные имена вроде `token`.
- Для Bitrix REST не угадывать методы, поля и payload по памяти. Проверять через `bitrix-mcp-rest`.

## Рекомендуемая раскладка

Для новой синхронизации создавать отдельный пакет, например:

```text
erp_xxx_replacement/
    sync_entity/
        payload.py
        projection.py
        source.py
        mapper.py
        target.py
```

Если синк заменяет большой procedural-файл, сначала собрать новый пакет рядом, не ломая старую точку входа.

## Payload

`Payload` отвечает за нормализованные данные из источника.

- Делай `@dataclass(frozen=True, slots=True)`.
- Класть сюда только данные и предметные helper-методы.
- Не писать отсюда в Bitrix, БД и внешние API.
- Версионирование строить через `utils.sync_core.dto.Payload`, а не вручную.
- Если синк по `updated_at`, инкапсулировать сравнение в payload-методе вроде `is_modified_after(dt)`.
- Если есть преобразования исходных кодов в бизнес-значения, держать их здесь, если они относятся к самой сущности.

Пример:

```python
@dataclass(frozen=True, slots=True)
class FooSyncPayload:
    external_id: int
    modified_at: datetime
    name: str

    def is_modified_after(self, dt: datetime | None) -> bool:
        return dt is None or self.modified_at > dt
```

Используй payload для:

- сравнения по дате изменения
- вычисления display name
- преобразования enum/code -> domain value

Не используй payload для:

- HTTP-запросов
- получения id справочников Bitrix
- batch enqueue

## Projection

`Projection` описывает ровно то, что будет записано в target.

Для Bitrix dynamic item это означает:

- описать все поля, которые пойдут в `fields`
- дать явные атрибуты с понятными именами
- сделать `to_dict()`, который возвращает готовый `fields` payload

`Projection` не должна быть "тонкой обёрткой". Если target пишет 20 полей, projection должна явно описывать эти 20 полей.

Если есть file-поля, они тоже должны входить в projection. Не выноси обновление файлов в отдельный target-step, если Bitrix позволяет отправить их вместе.

Пример:

```python
@dataclass(frozen=True, slots=True)
class FooProjection:
    title: str
    parent_id: int
    layout_file: list[str] | None

    def to_dict(self) -> dict[str, object]:
        fields = {
            FooObject.title.field_code: self.title,
            FooObject.parent.field_code: self.parent_id,
            FooObject.layout.field_code: self.layout_file,
        }
        return {field_code: value for field_code, value in fields.items() if value is not None}
```

## Source

`Source` получает данные из внешней системы и строит пары:

- `ExternalKey`
- `Payload`

Для реальных потоков использовать `utils.sync_core.base_source.BaseSource`.

### Правила Source

- Наследоваться от `BaseSource`.
- Выбирать `checkpoint_type` через `CheckpointType`.
- Использовать встроенное версионирование и форматирование чекпоинта из `BaseSource`.
- Делать `_fetch()` читаемым: только pagination, фильтрация по checkpoint и сбор item.
- Использовать `paginate_iter()`, если элементов может быть много.
- Не загружать все элементы сразу, если можно стримить страницами.
- В `validate()` делать техническую проверку payload.
- Разбивать мелкие части в private helpers, если это упрощает чтение.

### Pagination

Если внешний API или обход по родительским сущностям постраничный:

- делать маленький `fetch_page(page_token) -> (items, next_token)`
- передавать его в `paginate_iter()`
- возвращать generator, а не готовый список, если поток может быть большим

Если checkpoint известен только после обхода генератора, возвращать из `_fetch()` callable:

```python
return items, lambda: latest_modified_at
```

Это нужно, чтобы `BaseSource` отформатировал checkpoint после фактического обхода всех элементов.

### Чистый шаблон Source

```python
class FooSource(BaseSource[FooSyncPayload]):
    STREAM = "foo"

    def __init__(self, *, api: FooApi):
        super().__init__(
            checkpoint_type=CheckpointType.UPDATED_AT,
            checkpoint_required=False,
        )
        self.api = api

    def _fetch(self, parsed_checkpoint: datetime | None):
        parent_ids = list(self._iter_parent_ids())
        latest_modified_at = parsed_checkpoint

        def _fetch_page(page_token: str | None) -> tuple[list[SourceItem], str | None]:
            nonlocal latest_modified_at

            start = self._parse_page_token(page_token)
            page_parent_ids = parent_ids[start:start + 50]
            if not page_parent_ids:
                return [], None

            page_items: list[SourceItem] = []
            for raw_item in self.api.list_items(page_parent_ids):
                payload_data = FooSyncPayload.from_external(raw_item)
                if not payload_data.is_modified_after(parsed_checkpoint):
                    continue
                if payload_data.is_modified_after(latest_modified_at):
                    latest_modified_at = payload_data.modified_at
                page_items.append(self._build_item(payload_data))

            next_start = start + 50
            next_token = None if next_start >= len(parent_ids) else str(next_start)
            return page_items, next_token

        items, _ = self.paginate_iter(start_token=None, fetch_page=_fetch_page)
        return items, lambda: latest_modified_at
```

### Что держать в Source

- технический обход внешнего API
- pagination
- преобразование raw -> payload
- сбор `ExternalKey`
- техническую валидацию

### Что не держать в Source

- Bitrix mapping
- lookup id справочников Bitrix
- запись в target
- procedural бизнес-логику, не связанную с извлечением данных

## Mapper

`Mapper` получает `Payload` и строит `Projection`.

### Правила Mapper

- Не писать во внешние системы.
- Делать `validate()` отдельно от `map()`.
- В `validate()` проверять бизнес-корректность входа.
- В `map()` строить target-ориентированную projection.
- Возвращать `Projection(kind=..., data=...)`.
- Для сетевых/Bitrix lookup-проблем кидать `TemporaryMappingError`.
- Для некорректных бизнес-данных кидать `PermanentMappingError`.

### Что обычно находится в Mapper

- поиск связанных Bitrix id
- преобразование display values в enum/list value ids
- сбор файловых полей в формат Bitrix
- кеширование lookup-таблиц

Если нужно скачать несколько файлов, а это заметно тормозит sync, разрешено локально использовать `ThreadPoolExecutor`. Делать это просто, без отдельного слоя абстракций.

Пример подхода:

```python
def _load_file_fields(
    self,
    payload_data: FooSyncPayload,
) -> tuple[BitrixFileValue | None, BitrixMultiFileValue | None]:
    paths = [path for path in payload_data.file_paths if path is not None]
    if not paths:
        return None, None

    with ThreadPoolExecutor(max_workers=min(4, len(paths))) as executor:
        file_values = executor.map(self._file_to_bitrix_required, paths)
        files_by_path = dict(zip(paths, file_values))

    return files_by_path[paths[0]], [files_by_path[path] for path in paths[1:]] or None
```

## Target

`Target` получает один элемент за раз. Это нормально.

Если запись в приёмник должна быть батчевой, не пытайся переделать `sync_core` в multi-item target. Вместо этого:

- в `upsert()` ставь команду в очередь
- реальную batch-отправку делай отдельно по крону
- в `sync_core` возвращай deferred-результат

### Правила Target

- `validate()` проверяет только пригодность projection к записи.
- `upsert()` не должен содержать длинную procedural-логику.
- Если запись мгновенная, возвращать `TargetUpsertResult.completed(internal_id=...)`.
- Если запись отложенная, возвращать `TargetUpsertResult.deferred(command_id=...)`.
- Для deferred-таргета не использовать `wait_result()` внутри sync pipeline.
- Не вызывать `process_pending_bitrix_batch_commands()` из target. Это работа cron.

### Bitrix target для dynamic item

Перед сборкой params обязательно проверять метод через `bitrix-mcp-rest`.

Для `crm.item.add` использовать:

```python
params = {
    "entityTypeId": SpaceItemObject.ENTITY_TYPE_ID,
    "fields": projection.data.to_dict(),
}
```

Для `crm.item.update` использовать:

```python
params = {
    "entityTypeId": SpaceItemObject.ENTITY_TYPE_ID,
    "id": int(binding.internal_id),
    "fields": projection.data.to_dict(),
}
```

Не разносить file-поля в отдельный update, если они уже входят в `projection.data.to_dict()`.

## Deferred target через utils.bitrix_batch

Использовать `utils.bitrix_batch`, когда:

- target получает элементы по одному
- запись в Bitrix выгодно отправлять пачками
- обработка batch-команд идёт по крону

### Модель очереди

`BitrixBatchCommand` уже является моделью очереди.

Использовать её как основную точку API:

- `enqueue(...)`
- `enqueue_many(...)`
- `wait_result(...)` для единичных imperative-сценариев
- `mark_processing()`
- `mark_success()`
- `mark_error()`

Не строить вокруг неё лишний OO-слой без необходимости.

### QuerySet

Запросы к очереди выносить в кастомный queryset модели.

Минимально нужны:

- `pending()`
- `ordered_for_processing()`
- `lock_pending()`

`lock_pending()` может использовать:

```python
select_for_update(skip_locked=True)
```

Это нужно, чтобы два cron worker не взяли одни и те же pending-команды одновременно.

### delay_seconds

Для накопления команд перед batch-отправкой использовать `delay_seconds`.

Смысл:

- `enqueue(..., delay_seconds=300)` ставит запись в очередь сразу
- но cron сможет взять её только после наступления `processable_at`
- за это время похожие команды успеют накопиться и уйти в один batch

Это лучше, чем отправлять каждую команду сразу и терять batching.

### Runner

Runner должен быть маленьким.

Нормальный объём ответственности:

- забрать необработанные команды
- заблокировать их
- пометить как `PROCESSING`
- собрать один `BitrixCommandBatch`
- вызвать `but.batch_api_call(...)`
- разложить ответы по моделям

Не делать вручную внешние chunks поверх `batch_api_call`, если внутренний helper и так режет по стандартному размеру batch.

Допустим небольшой helper-класс вроде `BitrixCommandBatch`, если он реально делает код чище:

- хранит `commands`
- даёт property `but`
- умеет `process()`

Но не превращай runner в мини-фреймворк.

## Callback завершения deferred-команды

Для `sync_core` deferred-таргета основной способ завершения синка не `wait_result()`, а callback.

### Почему не wait_result в sync target

Если в target после `enqueue()` сразу ждать:

```python
command.wait_result(...)
```

то sync начнёт обрабатывать элементы последовательно:

- поставил 1 команду
- дождался
- поставил 2 команду
- дождался

Так batching ломается.

Правильный подход:

- target только ставит команду в очередь
- `SyncJob` идёт обрабатывать следующие элементы
- cron отправляет накопившиеся команды в Bitrix пачкой
- callback закрывает item state, binding и ошибки

### Требования к callback

- callback должен быть top-level importable function
- путь до callback хранится в `BitrixBatchCommand.callback_path`
- контекст синка хранить в `command.context`

Обычно достаточно положить в context:

```python
{
    "sync_system": key.system,
    "sync_ext_key": key.key,
    "sync_version": version,
}
```

### Что делать в callback

- восстановить `ExternalKey`
- получить `version`
- взять `DefaultStateStore`
- определить attempts из предыдущего item state
- при успехе сохранить binding и `SUCCESS`
- при ошибке определить `TEMP_ERROR` или `PERM_ERROR`
- записать новый `SyncItemState`

Повторяющуюся механику инкапсулируй в маленькие helper-методы и model/store API:

- `command.is_success`
- `command.get_crm_item_id()`
- `command.get_error_code()`
- `state_store.set_item_state(...)`

Не дублируй низкоуровневую логику по всему callback телу.

### Шаблон callback

```python
def complete_foo_sync(command: BitrixBatchCommand) -> None:
    key, version, state_store, attempts = _get_sync_context(command)

    try:
        if not command.is_success:
            state_store.set_item_state(
                key=key,
                version=version,
                status=_resolve_command_error_status(command),
                attempts=attempts,
                last_error=command.error,
            )
            return

        internal_id = command.get_crm_item_id()
        state_store.bind(key, internal_id, version)
        state_store.set_item_state(
            key=key,
            version=version,
            status=SyncItemStatus.SUCCESS,
            attempts=attempts,
            last_error=None,
        )
    except Exception as exc:
        state_store.set_item_state(
            key=key,
            version=version,
            status=SyncItemStatus.TEMP_ERROR,
            attempts=attempts,
            last_error=str(exc),
        )
        raise
```

## Sync state и результат target

Для target всегда использовать единый return type:

- `TargetUpsertResult.completed(...)`
- `TargetUpsertResult.deferred(...)`

Не возвращать из target то `str`, то `tuple`, то ещё что-то.

В `SyncJob` deferred target означает:

- item получает `SyncItemStatus.PENDING`
- checkpoint не должен продвинуться как полностью безопасный, пока остаются `PENDING` или retryable `TEMP_ERROR`

Не переписывай `SyncJob` радикально ради нового sync. Если нужен deferred-flow, расширяй существующий контракт маленькими изменениями.

## Validation policy по слоям

Распределяй проверки так:

- `Source.validate()`:
  - техническая корректность
  - обязательные id
  - пустые ключи
  - наличие version
- `Mapper.validate()`:
  - бизнес-корректность
  - наличие связанных сущностей в target-модели
  - валидность справочных значений
- `Target.validate()`:
  - пригодность projection к записи
  - `projection.kind`
  - корректность binding/internal_id

Если данные неверны по смыслу и retry не поможет, кидать permanent error.
Если проблема во внешнем API, сети или временной недоступности Bitrix, кидать temporary error.

## Практический шаблон для нового sync

1. Создать пакет `sync_entity`.
2. Описать `Payload` как нормализованную dataclass.
3. Описать `Projection` со всеми target fields и `to_dict()`.
4. Реализовать `Source` на `BaseSource` с incremental pagination.
5. Реализовать `Mapper` без side effects.
6. Реализовать `Target`, который либо пишет сразу, либо ставит deferred-команду в `BitrixBatchCommand`.
7. Для deferred-таргета сделать top-level callback завершения.
8. Использовать `DefaultStateStore`, если нет причины вводить отдельный store.
9. Проверить Bitrix REST method и params через MCP перед кодом.
10. Только после этого подключать sync job в точку запуска.

## Что считать хорошим результатом

Хороший sync в этом проекте выглядит так:

- `Source` короткий и читаемый
- pagination ленивый
- версия строится через `Payload`/`BaseSource`
- `Payload` знает, как сравнивать свои изменения
- `Projection` явно описывает target fields
- `Mapper` не пишет во внешние системы
- `Target` тонкий
- batch-логика вынесена в `utils.bitrix_batch`
- callback корректно закрывает `binding` и `item_state`
- `SyncJob` не переписан без необходимости

## Антипаттерны

Избегать:

- procedural transfer-функции на сотни строк
- target, который сам ждёт каждую команду через `wait_result()`
- projection без явных полей и без `to_dict()`
- source, который сначала загружает всё в память, а потом фильтрует
- ручного форматирования checkpoint, если это уже умеет `BaseSource`
- лишних классов-обёрток вокруг batch queue
- запросов очереди вне queryset, если они повторяются
- отдельной записи file-полей, если их можно отправить вместе
- неявных fallback-цепочек "попробуй этот ключ, потом тот"
- угадывания Bitrix REST params без проверки в docs

## Короткий чеклист перед завершением задачи

- Проверен ли Bitrix REST method через `bitrix-mcp-rest`?
- Есть ли у payload явный способ сравнить изменение?
- Есть ли у projection полный `to_dict()` для target fields?
- Стримит ли source данные страницами?
- Не делает ли mapper side effects?
- Не ждёт ли target каждую batch-команду синхронно?
- Обновляет ли callback `binding` и `SyncItemState`?
- Достаточен ли `delay_seconds`, чтобы команды успевали накопиться?
- Вынесены ли запросы очереди в queryset?
