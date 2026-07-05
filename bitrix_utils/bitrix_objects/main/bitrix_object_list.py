from django.core.serializers.json import DjangoJSONEncoder

import json
from typing import Any, Union, List, Text, Dict, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from utils.bitrix_utils.bitrix_objects.main.bitrix_object import BitrixObject


class BitrixObjectList(list):
    """Список BitrixObject с утилитами (length, to_ids, fetch/select_related).

    Examples:
        >>> objs = TaskObject.objects(but).all()
        >>> objs.to_ids()
    """

    def __str__(self):
        return f"{self.__class__.__name__}({super().__str__()})"

    def __repr__(self):
        return f"{self.__class__.__name__}({super().__repr__()})"

    def __getitem__(self, item: Any) -> Union["BitrixObjectList", Any]:
        value = super().__getitem__(item)

        if isinstance(value, list):
            return BitrixObjectList(value)
        else:
            return value

    def copy(self) -> "BitrixObjectList":
        return BitrixObjectList(super().copy())

    @property
    def length(self) -> int:
        return len(self)

    def to_ids(self) -> List[int]:
        """ID Битрикс-объектов"""
        return [bitrix_object.bitrix_id for bitrix_object in self]

    def fetch(self, **kwargs) -> "BitrixObjectList":
        if self.exists():
            bitrix_object = self.first()
            return bitrix_object.objects(bitrix_object.but).from_ids(self.to_ids(), **kwargs)
        else:
            return self.__class__()

    def set_select_related(self,
                           select_only: Optional[List[Text]] = None,
                           select_related: Optional[List[Text]] = None):

        if self.exists():
            bitrix_object = self.first()
            bitrix_object.objects(bitrix_object.but).set_select_related(self, select_only=select_only, select_related=select_related)

    def to_dicts(self,
                 select_only: Optional[List[Text]] = None,
                 select_related: Optional[List[Text]] = None,
                 prefetch_related: bool = True) -> List[Dict]:
        """Получение объекта, готового для сериализации"""

        if prefetch_related:
            self.set_select_related(select_only=select_only, select_related=select_related)

        return [bitrix_object.to_dict(select_only=select_only, select_related=select_related, prefetch_related=False) for bitrix_object in self]

    def to_json(self,
                select_only: Optional[List[Text]] = None,
                select_related: Optional[List[Text]] = None,
                prefetch_related: bool = True) -> Text:
        """Получение json строки со списком словарей с полями объекта"""
        return json.dumps(self.to_dicts(select_only=select_only, select_related=select_related, prefetch_related=prefetch_related), ensure_ascii=False, cls=DjangoJSONEncoder)

    def exists(self) -> bool:
        """Содержится ли хотя бы 1 элемент в списке"""
        return bool(self)

    def first(self) -> Optional["BitrixObject"]:
        if self.exists():
            return self[0]
        else:
            return None

    def last(self) -> Optional["BitrixObject"]:
        if self.exists():
            return self[-1]
        else:
            return None

    def filter(self, **kwargs) -> "BitrixObjectList":
        """Фильтрация по значением Битрикс полей"""

        from utils.bitrix_utils.bitrix_objects.main import BitrixObject

        def is_filtred(bitrix_object: BitrixObject) -> bool:
            for field_attr, field_value in kwargs.items():
                bitrix_field = getattr(bitrix_object, field_attr)
                if not bitrix_field.value == field_value:
                    return False
            return True

        return self.__class__(filter(is_filtred, self))

    def exclude(self, **kwargs) -> "BitrixObjectList":
        """Исключение по значением Битрикс полей"""

        from utils.bitrix_utils.bitrix_objects.main import BitrixObject

        def is_filtred(bitrix_object: BitrixObject) -> bool:
            for field_attr, field_value in kwargs.items():
                bitrix_field = getattr(bitrix_object, field_attr)
                if bitrix_field.value == field_value:
                    return False
            return True

        return self.__class__(filter(is_filtred, self))

    def values_list(self, *field_attrs, flat: bool = False) -> List:
        if len(field_attrs) == 0:
            raise TypeError("Необходимо указать хотя бы 1 атрибут")

        if flat and len(field_attrs) > 1:
            raise TypeError("При flat=True нельзя указывать больше 1 атрибута")

        if flat:
            field_attr = field_attrs[0]
            return [getattr(bitrix_object, field_attr).value for bitrix_object in self]
        else:
            return [(getattr(bitrix_object, field_attr).value for field_attr in field_attrs) for bitrix_object in self]
