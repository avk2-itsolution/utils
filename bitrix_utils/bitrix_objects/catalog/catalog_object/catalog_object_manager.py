from utils.bitrix_utils.bitrix_objects.main.bitrix_object_manager import BitrixObjectManager
from utils.bitrix_utils.bitrix_objects.main.bitrix_object_list import BitrixObjectList

from typing import Dict, Iterable, Optional, List, Text, Type, TYPE_CHECKING

if TYPE_CHECKING:
    from utils.bitrix_utils.bitrix_objects.catalog.catalog_object import CatalogObject


class CatalogObjectManager(BitrixObjectManager):
    """Менеджер объектов каталога с обертками над REST ``catalog.*``."""

    BITRIX_OBJECT_CLASS: Type["CatalogObject"]

    def get_fields(self) -> Dict:
        """Возвращает метаданные полей через ``catalog.*.getFields``."""
        result = self.but.call_list_method(self._fields_method)
        return self._validate_api_fields(result)

    def add(self, fields: Dict) -> int:
        """Создает сущность через ``catalog.{entity_type}.add`` и возвращает ее ID.

        Обязательные параметры:
        - fields: словарь полей сущности (зависит от типа catalog.*).
        """
        result = self.but.call_api_method(self._add_method, {"fields": fields})["result"]
        return self._validate_api_add(result)

    def all(self,
            order_dict: Optional[Dict] = None,
            select_list: Optional[Iterable] = None,
            select_only: Optional[List[Text]] = None,
            select_related: Optional[List[Text]] = None,
            timeout: Optional[int] = None) -> BitrixObjectList["CatalogObject"]:
        """Возвращает все сущности типа без фильтра."""
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
               timeout: Optional[int] = None) -> BitrixObjectList["CatalogObject"]:
        """Возвращает сущности по фильтру Bitrix24, поддерживает select/select_related."""
        fields = {"filter": filter_dict}

        if order_dict:
            fields.update({"order": order_dict})

        select_list = self.mix_select_list_and_select_only(select_list, select_only)

        if select_list:
            fields.update({"select": select_list})

        catalogs = self.but.call_list_method(self._list_method, fields, timeout=timeout)
        catalogs = self._validate_api_list(catalogs)

        catalog_objects = BitrixObjectList(self.BITRIX_OBJECT_CLASS(catalog[self.BITRIX_OBJECT_CLASS.ID_FIELD_CODE], but=self.but, bitrix_data=catalog) for catalog in catalogs)

        if select_related:
            self.set_select_related(catalog_objects, select_only=select_only, select_related=select_related)

        return catalog_objects

    def from_ids(self,
                 catalog_ids: Iterable[int],
                 order_dict: Optional[Dict] = None,
                 select_list: Optional[Iterable] = None,
                 select_only: Optional[List[Text]] = None,
                 select_related: Optional[List[Text]] = None,
                 timeout: Optional[int] = None) -> BitrixObjectList["CatalogObject"]:
        """Получает сущности по списку ID с теми же опциями выборки, что и ``filter``."""
        if catalog_ids:
            filter_dict = {self.BITRIX_OBJECT_CLASS.ID_FIELD_CODE: list(catalog_ids)}
            return self.filter(filter_dict=filter_dict,
                               order_dict=order_dict,
                               select_list=select_list,
                               select_only=select_only,
                               select_related=select_related,
                               timeout=timeout)
        else:
            return BitrixObjectList()

    @property
    def entity_type(self) -> Text:
        """Тип CRM-сущности."""
        return self.BITRIX_OBJECT_CLASS.entity_type

    @property
    def _fields_method(self) -> Text:
        return f"catalog.{self.entity_type}.getFields"

    @property
    def _add_method(self) -> Text:
        return f"catalog.{self.entity_type}.add"

    @property
    def _list_method(self) -> Text:
        return f"catalog.{self.entity_type}.list"
