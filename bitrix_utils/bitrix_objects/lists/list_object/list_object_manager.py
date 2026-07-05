from utils.bitrix_utils.bitrix_objects.main.bitrix_object_manager import BitrixObjectManager
from utils.bitrix_utils.bitrix_objects.main.exceptions import MultipleObjectsReturned
from utils.bitrix_utils.bitrix_objects.main.bitrix_object_list import BitrixObjectList


import time
from typing import Dict, Type, TYPE_CHECKING, Text, Optional, Iterable, List, Tuple

if TYPE_CHECKING:
    from utils.bitrix_utils.bitrix_objects.lists.list_object import ListObject


class ListObjectManager(BitrixObjectManager):
    """Менеджер элементов списков/УС (нужен IBLOCK_ID/TYPE в наследнике).

    Examples:
        >>> elems = DealList.objects(but).filter({"CREATED_BY": but.user_id})
        >>> created, is_new = DealList.objects(but).get_or_create({"CODE": "ABC"}, {"NAME": "Demo"})
    """

    BITRIX_OBJECT_CLASS: Type["ListObject"]

    def get_fields(self) -> Dict:
        result = self.but.call_list_method("lists.field.get", {
            "IBLOCK_TYPE_ID": self.BITRIX_OBJECT_CLASS.IBLOCK_TYPE_ID,
            "SOCNET_GROUP_ID": self.BITRIX_OBJECT_CLASS.SOCNET_GROUP_ID,
            "IBLOCK_ID": self.BITRIX_OBJECT_CLASS.IBLOCK_ID
        })
        return self._validate_api_fields(result)

    def add(self, fields: Dict, element_code: Optional[Text] = None) -> int:
        """Создает элемент списка и возвращает его ID.

        Обязательные параметры ``lists.element.add``:
        - IBLOCK_TYPE_ID: тип инфоблока (например, ``lists``).
        - IBLOCK_ID: ID инфоблока (указан в классе).
        - FIELDS: словарь полей.
        - ELEMENT_CODE: код элемента (если не передан — используется timestamp).
        """
        result = self.but.call_api_method("lists.element.add", {
            "IBLOCK_TYPE_ID": self.BITRIX_OBJECT_CLASS.IBLOCK_TYPE_ID,
            "ELEMENT_CODE": element_code or str(time.time()),
            "IBLOCK_ID": self.BITRIX_OBJECT_CLASS.IBLOCK_ID,
            "SOCNET_GROUP_ID": self.BITRIX_OBJECT_CLASS.SOCNET_GROUP_ID,
            "FIELDS": fields
        })["result"]
        return self._validate_api_add(result)

    def create(self, fields: Dict, element_code: Optional[Text] = None) -> "ListObject":
        """Добавить и получить элемент списка"""
        bitrix_id = self.add(fields, element_code)
        return self.BITRIX_OBJECT_CLASS(bitrix_id, but=self.but)

    def all(self,
            order_dict: Optional[Dict] = None,
            select_list: Optional[Iterable] = None,
            select_only: Optional[List[Text]] = None,
            select_related: Optional[List[Text]] = None,
            timeout: Optional[int] = None) -> BitrixObjectList["ListObject"]:
        """Все элементы"""
        filter_dict = {}
        return self.filter(
            filter_dict=filter_dict,
            order_dict=order_dict,
            select_list=select_list,
            select_only=select_only,
            select_related=select_related,
            timeout=timeout)

    def filter(self,
               filter_dict: Dict,
               order_dict: Optional[Dict] = None,
               select_list: Optional[Iterable] = None,
               select_only: Optional[List[Text]] = None,
               select_related: Optional[List[Text]] = None,
               timeout: Optional[int] = None) -> BitrixObjectList["ListObject"]:
        """Элементы по фильтру"""
        fields = {"IBLOCK_TYPE_ID": self.BITRIX_OBJECT_CLASS.IBLOCK_TYPE_ID, "IBLOCK_ID": self.BITRIX_OBJECT_CLASS.IBLOCK_ID, "SOCNET_GROUP_ID": self.BITRIX_OBJECT_CLASS.SOCNET_GROUP_ID}

        if filter_dict:
            fields.update({"FILTER": filter_dict})

        if order_dict:
            fields.update({"ELEMENT_ORDER": order_dict})

        select_list = self.mix_select_list_and_select_only(select_list, select_only)

        if select_list:
            fields.update({"SELECT": select_list})

        elements = self.but.call_list_method("lists.element.get", fields, timeout=timeout)
        elements = self._validate_api_list(elements)

        list_objects = BitrixObjectList(self.BITRIX_OBJECT_CLASS(element["ID"], but=self.but, bitrix_data=element) for element in elements)

        if select_related:
            self.set_select_related(list_objects, select_only=select_only, select_related=select_related)

        return list_objects

    def from_ids(self,
                 element_ids: Iterable[int],
                 order_dict: Optional[Dict] = None,
                 select_list: Optional[Iterable] = None,
                 select_only: Optional[List[Text]] = None,
                 select_related: Optional[List[Text]] = None,
                 timeout: Optional[int] = None) -> BitrixObjectList["ListObject"]:
        """Элементы по ID"""
        if element_ids:
            filter_dict = {"ID": list(element_ids)}
            return self.filter(
                filter_dict=filter_dict,
                order_dict=order_dict,
                select_list=select_list,
                select_only=select_only,
                select_related=select_related,
                timeout=timeout)
        else:
            return BitrixObjectList()

    def get_or_create(self,
                      filter_dict: Dict,
                      default_fields: Optional[Dict] = None,
                      element_code: Optional[Text] = None,
                      ignore_multiple: bool = False,
                      filter_after_api: Optional[Dict] = None) -> Tuple["ListObject", bool]:
        """Ищет элемент УС на портале по полям из filter_dict,
        если не находит, то создает с полями из filter_dict и default_fields"""

        if default_fields is None:
            default_fields = {}

        list_objects = self.filter(filter_dict)

        if filter_after_api is not None:
            list_objects = list_objects.filter(**filter_after_api)

        if len(list_objects) > 1:
            if ignore_multiple:
                # берем последний элемент
                return list_objects[-1], False
            else:
                raise MultipleObjectsReturned("Найдено больше одного элемента списка")

        if len(list_objects) == 1:
            return list_objects[0], False

        return self.create(filter_dict | default_fields, element_code=element_code), True

    def update_or_create(self,
                         filter_dict: Dict,
                         default_fields: Optional[Dict] = None,
                         element_code: Optional[Text] = None,
                         ignore_multiple: bool = False,
                         filter_after_api: Optional[Dict] = None) -> Tuple["ListObject", bool]:
        """Ищет элемент УС на портале по полям из filter_dict,
        если находит, то обновляет поля из default_fields,
        если не находит, то создает с полями из filter_dict и default_fields"""

        if default_fields is None:
            default_fields = {}

        list_objects = self.filter(filter_dict)

        if filter_after_api is not None:
            list_objects = list_objects.filter(**filter_after_api)

        if list_objects.length > 1:
            if ignore_multiple:
                # берем последний элемент
                return list_objects.last(), False
            else:
                raise MultipleObjectsReturned("Найдено больше одного элемента списка")

        if list_objects.length == 1:
            list_object = list_objects.first()
            list_object.update(list_object.fields_to_bitrix | default_fields)
            return list_object, False

        return self.create(filter_dict | default_fields, element_code=element_code), True
