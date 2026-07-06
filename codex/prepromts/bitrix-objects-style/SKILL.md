---
name: bitrix-objects-style
description: "Используй для создания и доработки локальных Bitrix object классов в `bitrix_objects_local` на базе `utils.bitrix_utils`: смарт-процессы CRM, `CRMItemObject`, managers, field mapping, пользовательские поля UF_CRM, связи между смартами и проверка UTF-8."
---

# Bitrix Objects Style

Используй этот skill, когда нужно описать Bitrix24 сущность как Python object в `bitrix_objects_local` через `utils.bitrix_utils`.

Цель: получить тонкое локальное описание сущности Bitrix, которое удобно импортировать, читать и использовать в интеграциях. Не добавляй бизнес-сценарии в object-класс, если пользователь просит только описать поля.

## Перед Кодом

Сначала собери точные данные по смарту:

- URL или `entityTypeId`;
- `USER_FIELD_ENTITY_ID`, если есть настройки пользовательских полей;
- список полей из Б24: человекочитаемое название, системный код `UF_CRM_...`, тип, множественность;
- для связей: точный target smart/entity type, а не только название вкладки;
- пример соседнего object-класса и manager в проекте.

Не угадывай `entityTypeId`, target smart или тип связи. Если данных не хватает, либо оставь поле сырым, либо явно попроси недостающий `typeId`.

## Где Создавать

Для CRM smart process создавай отдельный пакет:

```text
bitrix_objects_local/
    crm/
        foo_item_object/
            __init__.py
            foo_item_object.py
            foo_item_object_manager.py
```

Один смарт — один object-класс. Не используй один класс для нескольких разных смартов только потому, что они похожи по названию.

## Базовый Шаблон

Object смарта наследуется от `CRMItemObject`, manager — от `CRMItemObjectManager`.

```python
from __future__ import annotations

from bitrix_objects_local.crm.foo_item_object.foo_item_object_manager import (
    FooItemObjectManager,
)
from utils.bitrix_utils.bitrix_objects.crm import CRMItemObject
from utils.bitrix_utils.bitrix_objects.main.fields import (
    IntBitrixField,
    TextBitrixField,
)


class FooItemObject(CRMItemObject):
    """Объект элемента смарта Foo."""

    ENTITY_TYPE_ID       = 1038
    ENTITY_TYPE_NAME     = CRMItemObject.get_entity_type_name(ENTITY_TYPE_ID)
    ENTITY_TYPE_ABBR     = CRMItemObject.get_entity_type_abbr(ENTITY_TYPE_ID)
    USER_FIELD_ENTITY_ID = "CRM_4"

    _objects             = FooItemObjectManager

    external_id = IntBitrixField("ufCrm4_1780901727")  # ID во внешней системе
    code        = TextBitrixField("ufCrm4_1780556058")  # Код услуги
```

Manager:

```python
from typing import TYPE_CHECKING, Type

from utils.bitrix_utils.bitrix_objects.crm import CRMItemObjectManager

if TYPE_CHECKING:
    from bitrix_objects_local.crm.foo_item_object import FooItemObject


class FooItemObjectManager(CRMItemObjectManager):
    """Менеджер элементов смарта Foo."""

    BITRIX_OBJECT_CLASS: Type["FooItemObject"]
```

## Поля

Для `crm.item.*` пользовательские поля записывай в camelCase формате API:

```text
UF_CRM_4_1780901727 -> ufCrm4_1780901727
```

У каждого поля обязателен короткий inline comment с названием поля из Б24:

```python
booking_id = IntBitrixField("ufCrm4_1781161710")  # booking_id
```

Комментарий должен быть именно человекочитаемым названием поля в Б24, а не системным кодом. Если название в Б24 техническое (`activity_id`, `resource_ids`) — оставь его как есть.

Подбирай field class по типу Б24:

- `Строка` -> `TextBitrixField`;
- `Число` -> `IntBitrixField` или `FloatBitrixField` по данным;
- `Дата` -> `DateBitrixField`;
- `Дата со временем` -> `DateTimeBitrixField`;
- `Да/Нет` -> `BoolBitrixField`;
- `Список` -> `ListBitrixField`;
- файл -> `FileBitrixField`, если это реально file field в API;
- множественное поле -> добавь `is_multiple=True`.

Если поле является raw ID, но target object неизвестен, не притворяйся связью:

```python
premises = TextBitrixField("ufCrm4_1783318913", is_multiple=True)  # Помещения
```

Когда target smart точно известен, используй `UfCrmObjectBitrixField`:

```python
required_documents = UfCrmObjectBitrixField(
    "ufCrm5_1782288082",
    object_type=RequiredDocumentItemObject,
    is_multiple=True,
)  # Необходимые документы
```

Для встроенных связей Bitrix вроде `assignedById`, `companyId`, `categoryId`, `parentId...` используй `ObjectBitrixField`, если значение является ID другой Bitrix object сущности.

## Связи Между Смартами

Если поле Б24 типа "Привязка к элементам CRM":

1. Найди точный target smart/entity.
2. Создай отдельный object-класс target смарта, если его ещё нет.
3. Импортируй target class в source object.
4. Используй `UfCrmObjectBitrixField(..., object_type=TargetObject, is_multiple=True/False)`.

Не связывай поле с object-классом по похожему русскому названию. Например, "Услуги", "Обязательные услуги" и "Рекомендованные услуги" могут быть разными смартами.

Если известна только ссылка на карточку элемента без `entityTypeId`, не выводи тип из URL соседней вкладки. Лучше оставить поле как `TextBitrixField` и отметить риск в финальном ответе.

## Имена И Форматирование

Имена Python-полей делай предметными и стабильными:

```python
appointment_start
required_services
service_code_804
required_documents
```

Выравнивание class-level assignments допустимо и полезно для object-классов, где много полей:

```python
service_code       = TextBitrixField("ufCrm5_1780556058")  # Код услуги
service_code_804   = TextBitrixField("ufCrm5_1780556077")  # Код услуги по 804-н
service_direction  = ListBitrixField("ufCrm5_1780556101")  # Направление услуги
```

Не выравнивай ради красоты внутри обычной бизнес-логики. Здесь это оправдано только потому, что object-класс является таблицей соответствия Б24 полей.

## Imports И __init__.py

Используй абсолютные импорты от `bitrix_objects_local` и `utils.bitrix_utils`.

Если в `bitrix_objects_local.crm.__init__` уже есть re-export локальных object-классов, добавь новый импорт в существующем стиле. Если re-export convention нет, не вводи её только ради нового класса.

Не добавляй `__all__`, если соседний код его не использует.

## Bitrix REST

Object-класс обычно не требует прямых вызовов REST. Если задача всё же включает чтение/запись в Bitrix:

- используй объект `but`;
- не придумывай method, params, payload и response shape;
- сначала проверь документацию через `bitrix-mcp-rest`;
- для `crm.item.add/update/list/get` проверяй `entityTypeId`, `fields`, `id` и форму ответа.

Для production portal используй только read-only доступ, если пользователь не дал отдельное разрешение на запись. Не используй admin webhook/token и write-capable token для диагностики.

## Проверка

После изменений проверь минимум:

```text
py -3 -B -c "from bitrix_objects_local.crm import FooItemObject; print(FooItemObject.ENTITY_TYPE_ID)"
rg -n "Р(?:џ|ћ|ё)|С(?:Ѓ|‚|Њ)" bitrix_objects_local
```

Если менял только preprompts, проверь новый `SKILL.md` на читаемый UTF-8 и mojibake.

`manage.py check` запускай только если локальные зависимости установлены. Если проверка падает на `psycopg`/`psycopg2`, это проблема окружения, а не самого object mapping.

Не оставляй новые `__pycache__` после import smoke, если они появились в рабочем дереве.

## Финальный Ответ

Коротко укажи:

- какие object-классы и manager добавлены;
- какие `entityTypeId` и `USER_FIELD_ENTITY_ID` использованы;
- какие связи сделаны object-связями, а какие оставлены raw из-за нехватки target type;
- какие проверки прошли;
- какие поля или связи требуют уточнения в Б24.
