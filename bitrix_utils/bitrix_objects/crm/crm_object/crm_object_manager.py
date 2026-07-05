from utils.bitrix_utils.bitrix_objects.main.bitrix_object_manager import BitrixObjectManager
from utils.bitrix_utils.bitrix_objects.main.bitrix_object_list import BitrixObjectList

from typing import Dict, Iterable, Optional, List, Text, Type, TYPE_CHECKING

if TYPE_CHECKING:
    from utils.bitrix_utils.bitrix_objects.crm.crm_object import CRMObject


class CRMObjectManager(BitrixObjectManager):
    """Менеджер объектов CRM с обертками над ``crm.*``.

    Examples:
        >>> deals = Deal.objects(but).filter({"ASSIGNED_BY_ID": but.user_id})
        >>> leads = Lead.objects(but).all()
    """

    BITRIX_OBJECT_CLASS: Type["CRMObject"]

    def get_fields(self) -> Dict:
        result = self.but.call_list_method(self._fields_method, {"entityTypeId": self.BITRIX_OBJECT_CLASS.ENTITY_TYPE_ID})
        return self._validate_api_fields(result)

    def get_cached_fields(self) -> Dict[Text, Dict]:
        """Кэшированные метаданные полей Bitrix-объекта."""
        if self.BITRIX_OBJECT_CLASS._fields is None:
            self.BITRIX_OBJECT_CLASS._fields = self.get_fields()
        return self.BITRIX_OBJECT_CLASS._fields

    def get_field_values(self, field_code: Text) -> List[Dict[Text, Text]]:
        """Варианты значений enum-поля."""
        field = self.get_cached_fields().get(field_code, {})
        return field.get("items", [])

    def value_to_id(self, field_code: Text) -> Dict[Text, Text]:
        """Возвращает словарь значение - id значения enum-поля."""
        values = self.get_field_values(field_code)
        return {str(value['VALUE']): str(value['ID']) for value in values if value.get('ID') and value.get('VALUE')}

    def get_field_value_id(self, field_code: Text, display_value: Optional[Text]) -> Optional[Text]:
        """Идентификатор enum-значения по его отображаемому названию."""
        if not display_value:
            return None
        return self.value_to_id(field_code).get(display_value)

    def get_field_value_ids(self, field_code: Text, display_values: list[Text]) -> list[Text]:
        """Идентификаторы enum-значения по его отображаемому названию."""
        value_ids = []
        for display_value in display_values:
            value_id = self.value_to_id(field_code).get(display_value)
            if value_id:
                value_ids.append(value_id)

        return value_ids

    def add(self, fields: Dict) -> int:
        """Создает CRM-элемент и возвращает его ID."""
        result = self.but.call_api_method(self._add_method, {"entityTypeId": self.BITRIX_OBJECT_CLASS.ENTITY_TYPE_ID, "fields": fields})["result"]
        return self._validate_api_add(result)

    def all(self,
            order_dict: Optional[Dict] = None,
            select_list: Optional[Iterable] = None,
            select_only: Optional[List[Text]] = None,
            select_related: Optional[List[Text]] = None,
            timeout: Optional[int] = None) -> BitrixObjectList["CRMObject"]:
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
               timeout: Optional[int] = None) -> BitrixObjectList["CRMObject"]:
        """Элементы по фильтру"""
        fields = {"entityTypeId": self.BITRIX_OBJECT_CLASS.ENTITY_TYPE_ID, "filter": filter_dict}

        if order_dict:
            fields.update({"order": order_dict})

        select_list = self.mix_select_list_and_select_only(select_list, select_only)

        if select_list:
            fields.update({"select": select_list})

        crms = self.but.call_list_method(self._list_method, fields, timeout=timeout)
        crms = self._validate_api_list(crms)

        crm_objects = BitrixObjectList(self.BITRIX_OBJECT_CLASS(crm[self.BITRIX_OBJECT_CLASS.ID_FIELD_CODE], but=self.but, bitrix_data=crm) for crm in crms)

        if select_related:
            self.set_select_related(crm_objects, select_only=select_only, select_related=select_related)

        return crm_objects

    def from_ids(self,
                 crm_ids: Iterable[int],
                 order_dict: Optional[Dict] = None,
                 select_list: Optional[Iterable] = None,
                 select_only: Optional[List[Text]] = None,
                 select_related: Optional[List[Text]] = None,
                 timeout: Optional[int] = None) -> BitrixObjectList["CRMObject"]:
        """Возвращает элементы по списку ID с теми же опциями выборки, что и ``filter``."""
        if crm_ids:
            filter_dict = {self.BITRIX_OBJECT_CLASS.ID_FIELD_CODE: list(crm_ids)}
            return self.filter(filter_dict=filter_dict,
                               order_dict=order_dict,
                               select_list=select_list,
                               select_only=select_only,
                               select_related=select_related,
                               timeout=timeout)
        else:
            return BitrixObjectList()

    def get_categories(self) -> BitrixObjectList["CRMObject.CATEGORY_OBJECT"]:
        """Получить воронки текущей CRM-сущности"""
        return self.BITRIX_OBJECT_CLASS.category_class.objects(self.but).all()

    @property
    def entity_type(self) -> Text:
        """Тип CRM-сущности"""
        return self.BITRIX_OBJECT_CLASS.entity_type

    @property
    def _fields_method(self) -> Text:
        return f"crm.{self.entity_type}.fields"

    @property
    def _add_method(self) -> Text:
        return f"crm.{self.entity_type}.add"

    @property
    def _list_method(self) -> Text:
        return f"crm.{self.entity_type}.list"
