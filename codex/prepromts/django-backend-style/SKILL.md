---
name: django-backend-style
description: "Используй для Python и Django backend задач в этом проекте: проектирование, рефакторинг и реализация доменной логики, Django models, QuerySet, services, DTO, integrations, Bitrix24 REST, sync_core, cron jobs, handlers, views и структуры файлов. Фиксирует предпочтительный стиль: минимальные правки, ясная доменная ответственность, мало кода, без лишних классов и слоёв, точная проверка Bitrix24 документации и безопасная работа с UTF-8 русским текстом."
---

# Django Backend Style

Используй этот skill для backend-задач в этом коде. Цель не в механическом применении паттерна, а в коде, который легко читать, менять и сопровождать.

Приоритет при спорных моментах:

1. Явные правки и замечания из текущего диалога.
2. `backend-design`.
3. `django-backend-design`.

## Рабочий стиль

Перед реализацией дай короткий план. Для крупных задач сначала объясни предметную модель и место, где должна жить логика.

Делай минимальные сфокусированные изменения. Не переписывай старый код, не удаляй существующие файлы и не меняй общие контракты без прямого запроса или необходимости для корректности.

Меньше кода лучше, чем больше, если оба решения одинаково корректны. Избегай и процедурной каши, и декоративного ООП.

Перед правкой читай соседний код. Следуй существующим паттернам проекта, если они не конфликтуют с правилами этого skill.

Если изменение в shared/core модуле полезно, сначала объясни зачем. Маленькие обоснованные правки допустимы, широкие переписывания — нет.

Пиши современный типизированный Python. Для DTO и immutable value objects предпочитай `dataclass(frozen=True, slots=True)`.

Докстринги — короткие и на русском. Комментарии должны объяснять причину, а не повторять код.

Файлы сохраняй в UTF-8 без BOM. Не перекодируй существующий русский текст. После правок файлов с кириллицей проверяй, что текст не превратился в mojibake.

## Сначала Предметная Область

Начинай с предметной области, а не с endpoint или структуры папок.

Перед кодом определи:

1. Какая здесь сущность или агрегат.
2. Какой объект владеет состоянием и бизнес-правилами.
3. Какие инварианты нужно защитить.
4. Где должна жить логика.
5. Нужен ли новый класс.

Не начинай проектирование от serializer, view, payload, mapper, validator, endpoint или технического шага.

## Классы

Не создавай класс только ради группировки кода или следования шаблону.

Класс нужен, только если он:

- хранит состояние или зависимости;
- защищает инварианты;
- имеет самостоятельный предметный смысл;
- имеет свой жизненный цикл;
- используется повторно в нескольких местах;
- реально уменьшает сложность.

Перед добавлением класса проверь, можно ли сделать поведение:

- методом существующей сущности;
- приватным helper-методом текущего класса;
- простой функцией;
- методом queryset;
- маленьким DTO.

Если новый класс — просто технический шаг, он не нужен.

## Django Models И QuerySet

Django model хранит persisted state, локальные бизнес-правила и переходы состояния.

Хорошие model-методы:

```python
order.confirm()
photo.mark_synced()
product.has_pending_materials()
```

Предметные выборки держи в custom `QuerySet`:

```python
pending()
for_sync()
latest_versions()
lock_pending()
```

Не размещай в моделях длинные сценарии и вызовы нескольких внешних систем.

Для частых проверок состояния используй model property, например `command.is_success`, вместо повторения прямых сравнений статуса.

Для статусов и стабильных choices используй `models.TextChoices` или похожую явную enum-структуру.

Для времени в Django-коде используй `django.utils.timezone`.

## Services И Use Cases

Application service координирует законченный бизнес-сценарий:

- модели и агрегаты;
- внешние интеграции;
- границы транзакции;
- возвращаемый DTO или результат.

Service не должен зависеть от `Request`, `Response` и HTTP-кодов.

Не создавай service или use-case class для каждого endpoint или маленького технического действия. Простая операция может быть функцией.

Use-case class нужен только когда один сценарий координирует несколько сущностей, внешние интеграции, транзакции или нетривиальную последовательность шагов.

Если сценарий работает внутри одного агрегата, предпочитай метод агрегата.

## Transport

Views, serializers, webhooks, robots, crons, tasks, handlers и management commands должны быть тонкими, но не искусственно пустыми.

Хорошие обязанности transport-слоя:

- прочитать и проверить вход;
- получить начальные объекты;
- вызвать доменный объект, service или use-case;
- преобразовать известные исключения в response;
- вернуть результат.

Плохие обязанности transport-слоя:

- защищать бизнес-инварианты;
- собирать сложное доменное состояние;
- содержать длинные ветвления бизнес-логики;
- знать детали нескольких внешних систем.

Бизнес-логика не должна жить во view или cron.

## DTO И Integrations

Используй DTO на реальных границах:

- ответы внешнего API;
- результаты парсинга;
- вход или результат сложного сценария;
- данные синхронизации.

Не протаскивай сырой внешний `dict` через приложение. Нормализуй данные рядом с границей.

Внешние API, Bitrix24, Kafka, файловые хранилища и похожие системы изолируй в клиентах или адаптерах. Клиент отвечает за транспорт, service — за бизнес-решения.

Передавай внешние зависимости через конструктор. Не создавай `Protocol`, repository, adapter или отдельный слой без практической необходимости.

Не злоупотребляй fallback-логикой. Избегай необоснованных `or default`, чтения одного значения из нескольких возможных ключей и проверок "на всякий случай". Если формат данных неясен, сначала уточни или изучи точную структуру.

## Обработка Ошибок

Не скрывай ошибки через `pass`, молчаливый fallback или необоснованный `return None`.

Лучше упасть с понятной ошибкой, чем продолжить с некорректными данными.

Разделяй:

- бизнес-ошибки;
- временные ошибки интеграции, которые можно повторить;
- постоянные ошибки данных.

`except Exception` допустим только на верхней границе с логированием или явной записью состояния.

При преобразовании ошибок в sync state держи mapping читаемым и явным.

## Bitrix24

Для `BitrixUserToken` используй имя `but`.

Пример:

```python
but.call_api_method("crm.activity.add", task_data)
```

Не придумывай Bitrix24 methods, fields, events, payload и response shape по памяти. Перед кодом проверяй документацию через `bitrix-mcp-rest`.

Для Bitrix dynamic item проверяй точные params перед реализацией. Например, `crm.item.add` и `crm.item.update` используют top-level `entityTypeId`, `fields`, а для update ещё и `id`.

Не выноси file fields в отдельный update, если Bitrix принимает их вместе с остальными fields.

## sync_core

Используй существующий `utils.sync_core` для сложной односторонней синхронизации, когда есть стабильный внешний ID и несколько условий:

- version, hash или `updated_at`;
- checkpoint или cursor;
- binding между внешним и внутренним ID;
- create/update;
- частичные ошибки;
- retry;
- продолжение после сбоя.

Нормальный flow:

```text
entrypoint -> SyncJob
              Source
              Mapper
              Target
              StateStore
              SyncLogger
```

Используй `sync_core` только когда сложность синка это оправдывает. Для простой интеграции из одного-двух действий предпочитай:

```text
entrypoint -> service -> client/model
```

Перед реализацией sync назови:

- `ExternalKey`;
- version;
- checkpoint;
- binding;
- temporary и permanent errors;
- способ обеспечения идемпотентности.

Собирай `SyncJob` только в cron или management command.

## sync_core Source

`Source` получает внешние данные, создаёт `ExternalKey` и `Payload`, выполняет техническую валидацию.

Для реальных потоков наследуйся от `BaseSource`.

Используй готовые возможности `BaseSource` для checkpoint parsing, formatting и pagination. Не делай ручное версионирование и форматирование checkpoint, если base class уже это умеет.

Используй ленивую pagination через `paginate_iter()`, если поток может быть большим. Не загружай всё в память, если данные можно отдавать страницами.

Держи `_fetch()` сфокусированным на pagination, фильтрации по checkpoint и сборке item.

Если checkpoint известен только после обхода iterator, возвращай callable checkpoint:

```python
return items, lambda: latest_modified_at
```

Сравнение modified time инкапсулируй в payload data:

```python
payload_data.is_modified_after(parsed_checkpoint)
```

## sync_core Payload

`Payload` — это нормализованные данные источника.

Используй `@dataclass(frozen=True, slots=True)`.

Держи внутри payload только данные и доменные helper-методы. Не делай там HTTP-запросы, Bitrix lookups, DB writes или queue writes.

Строй payload version через `utils.sync_core.dto.Payload`, например `Payload.with_version_from_datetime(...)`.

Для `updated_at` sync добавляй метод вида:

```python
def is_modified_after(self, dt: datetime | None) -> bool:
    return dt is None or self.modified_at > dt
```

## sync_core Projection

`Projection` описывает то, что будет записано в target.

Для Bitrix target fields projection должна явно перечислять все fields, которые могут быть отправлены в Bitrix, и иметь `to_dict()`.

Не делай projection тонкой заглушкой. Если Bitrix получает `fields` по каждому item, projection владеет формой этих `fields`.

Пример:

```python
@dataclass(frozen=True, slots=True)
class FooSyncProjection:
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

## sync_core Mapper

`Mapper` применяет бизнес-правила и строит `Projection`.

Он не должен писать во внешние системы.

Используй `validate()` для бизнес-валидации, `map()` — для сборки projection.

Хорошие обязанности mapper:

- находить связанные Bitrix IDs;
- маппить display values в Bitrix enum/list IDs;
- собирать file values для Bitrix;
- кешировать lookup tables.

Для временных external/API проблем используй `TemporaryMappingError`. Для некорректных бизнес-данных, которые retry не исправит, используй `PermanentMappingError`.

Если нужно скачать несколько remote files и это заметно влияет на runtime, допустим маленький локальный `ThreadPoolExecutor`.

## sync_core Target

`Target` получает один item за раз. Сохраняй этот контракт.

Если записи нужно батчить, не превращай target в multi-item processor. Используй `utils.bitrix_batch`.

`Target.upsert()` должен возвращать один общий result type:

- `TargetUpsertResult.completed(internal_id=...)`;
- `TargetUpsertResult.deferred(command_id=...)`.

Не возвращай разные типы вроде иногда `str`, иногда `tuple`.

Не переписывай `SyncJob` широко ради нового target. Делай только маленькие обоснованные изменения контракта.

## Bitrix Batch Queue

Используй `utils.bitrix_batch`, когда sync target получает один item за раз, но записи в Bitrix нужно отправлять batch-ами.

Основной API должен быть на `BitrixBatchCommand`:

- поставить одну command;
- поставить несколько commands;
- дождаться результата, если это imperative-сценарий;
- пометить processing/success/error;
- дать properties и helpers вроде `is_success`, `get_crm_item_id()`, `get_error_code()`.

`wait_result()` используй только для imperative-сценариев. Не вызывай его из sync target, потому что так pipeline начнёт обрабатывать items последовательно и batching не сработает.

Для sync target должен поставить command в очередь и вернуть `TargetUpsertResult.deferred(...)`. Cron processing отправляет накопленные commands в Bitrix. Callback закрывает state и binding.

Используй `delay_seconds`, чтобы commands успевали накопиться до обработки cron-ом. Queryset должен фильтровать по `processable_at__lte=timezone.now()`.

Не группируй и не фильтруй batch processing по `but`, если пользователь явно этого не просил. Не оперируй `but_id`, когда достаточно самого объекта.

Не добавляй внешнее chunking, `_iter_chunks`, `chunk` или custom `batch_size` вокруг `batch_api_call`, если helper уже сам обрабатывает стандартный размер Bitrix batch.

Допустим небольшой `BitrixCommandBatch`, если он делает runner читаемее:

- хранит `commands`;
- имеет `fabric(...)`;
- отдаёт `but` как `self.commands[0].but`;
- вызывает `but.batch_api_call(..., timeout=timeout)`;
- распределяет successes и errors обратно по command models.

## Deferred Callback

Для deferred sync завершение должно быть в top-level importable callback function.

Минимальный sync context храни в `BitrixBatchCommand.context`:

```python
{
    "sync_system": key.system,
    "sync_ext_key": key.key,
    "sync_version": version,
}
```

Обязанности callback:

- восстановить `ExternalKey`;
- получить version и `DefaultStateStore`;
- прочитать предыдущие attempts;
- при success сохранить binding на Bitrix ID и `SUCCESS`;
- при error сохранить `TEMP_ERROR` или `PERM_ERROR`;
- явно записать callback failure и re-raise, когда нужно.

Повторяющуюся механику выноси в model или store helpers:

- `command.is_success`;
- `command.get_crm_item_id()`;
- `command.get_error_code()`;
- `state_store.set_item_state(...)`.

Callback должен читаться легко. Длинный callback обычно означает, что не хватает state extraction или command helpers.

## Структура Файлов

Группируй код по предметной области и агрегатам, а не по технической церемонии.

Используй только нужные директории. Предпочитай осмысленные папки:

```text
app/
    models/
    services/
    dto/
    integrations/
    sync/
    views/
    crons/
    tests/
```

Предпочитай `services`, `dto`, `integrations`, `sync`, `parsers`, `resolvers` расплывчатой папке `classes`.

В приложениях, где `classes/` уже есть, не используй её как свалку. Внутри должна быть предсказуемая структура по предметным понятиям.

Обычно один класс — один файл, но это не абсолютное правило. Маленькие тесно связанные value objects, exceptions или helper domain types можно держать вместе, если разделение ухудшит читаемость.

Не добавляй `__all__` и широкие re-export imports в package `__init__.py` без реальной локальной convention или необходимости публичного API. Такие импорты часто скрывают, где живёт код, и мешают навигации.

Не выноси constants в отдельный constants-file без явной пользы. Для стабильных именованных состояний предпочитай enum-like classes.

## Рефакторинг Существующего Кода

Когда разделяешь большой файл:

- сначала проанализируй responsibilities;
- перенеси связные части в focused files;
- сохрани поведение;
- избегай лишней абстракции;
- оставь старые entrypoints, если пользователь не просил удалить их.

Если функция выглядит процедурной и тяжело читается, сначала ищи одну-две domain operations или queryset method. Не заменяй процедурный код более крупной OO-иерархией.

Если helper, factory или маленький class делает runner или callback понятнее, добавь его. Если он только называет одну строку, не добавляй.

Повторяющиеся model queries выноси в custom queryset.

Частые проверки состояния выноси в model properties.

## Детали Кода

Используй понятные имена. Для Bitrix token variables используй `but`.

Используй полные читаемые method names. Избегай неясных сокращений вроде `wait_res`.

Не используй бесконечные циклы для polling. Используй timeout и ограниченное число attempts.

Предпочитай прямой явный доступ к данным вместо speculative fallback keys.

Если строка кода выглядит подозрительно, объясни её или упрости.

Выравнивание keyword arguments допустимо, если оно реально улучшает сканирование, но formatting tricks не заменяют простоту кода.

Не добавляй comments и docstrings, которые дублируют очевидный код.

## Формат Ответа

Для архитектурных задач перед кодом кратко объясняй:

1. Какая здесь сущность или агрегат.
2. Почему логика живёт именно там.
3. Нужен ли новый класс.
4. Почему это проще, чем дополнительная декомпозиция.

Для implementation tasks дай короткий план, затем внеси изменение, затем сообщи verification.

Финальный ответ держи коротким. Укажи изменённые файлы и запущенные проверки. Если tests не запускались, скажи об этом.

## Чеклист

Перед завершением backend-задачи проверь:

- Сохранён ли стиль соседнего кода?
- Понятно ли, кто владеет логикой в предметной области?
- Удалось ли избежать лишних classes, services, repositories и re-export imports?
- Вынесены ли повторяющиеся model queries в queryset?
- Скрыты ли частые state checks за понятными properties?
- Явны ли DTO и projection shapes?
- Нет ли silent fallback и `return None` для invalid data?
- Для Bitrix24 проверены ли REST method и params через docs?
- Для sync понятны ли `ExternalKey`, version, checkpoint, binding, retries и errors?
- Для batched Bitrix sync target ставит command в очередь, а callback завершает state?
- Остался ли русский текст читаемым в UTF-8?
