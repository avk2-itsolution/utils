from utils.bitrix_utils.bitrix_objects.catalog.catalog_object.catalog_object_manager import CatalogObjectManager
from utils.bitrix_utils.bitrix_objects.catalog.base_product_object.constants import SELECT_FIELDS
from utils.bitrix_utils.bitrix_objects.main.bitrix_object_list import BitrixObjectList

from typing import Type, TYPE_CHECKING, Dict, List, Optional, Text, Iterable

if TYPE_CHECKING:
    from utils.bitrix_utils.bitrix_objects.catalog import BaseProductObject


class BaseProductObjectManager(CatalogObjectManager):
    """Менеджер товаров с автоподстановкой ``IBLOCK_ID`` и дефолтным select.

    Examples:
        >>> products = Product.objects(but).by_section(section_id=1)
        >>> ids = [p.bitrix_id for p in products]
    """

    BITRIX_OBJECT_CLASS: Type["BaseProductObject"]

    def get_fields(self) -> Dict:
        """Возвращает описание полей товара через ``catalog.product.getFieldsByFilter``.

        Обязательные параметры:
        - filter.iblockId: ID инфоблока (``IBLOCK_ID`` класса).
        """
        result = self.but.call_list_method(self._fields_method, {"filter": {"iblockId": self.BITRIX_OBJECT_CLASS.IBLOCK_ID}})
        return self._validate_api_fields(result)

    def all(self,
            order_dict: Optional[Dict] = None,
            select_list: Optional[Iterable] = SELECT_FIELDS,
            select_only: Optional[List[Text]] = None,
            select_related: Optional[List[Text]] = None,
            timeout: Optional[int] = None) -> BitrixObjectList["BITRIX_OBJECT_CLASS"]:
        """Возвращает все товары с дефолтным набором полей."""
        return super().all(
            order_dict=order_dict,
            select_list=select_list,
            select_only=select_only,
            select_related=select_related,
            timeout=timeout)

    def filter(self,
               filter_dict: Dict,
               order_dict: Optional[Dict] = None,
               select_list: Optional[Iterable] = SELECT_FIELDS,
               select_only: Optional[List[Text]] = None,
               select_related: Optional[List[Text]] = None,
               timeout: Optional[int] = None) -> BitrixObjectList["BITRIX_OBJECT_CLASS"]:
        """Возвращает товары по фильтру, автоматически добавляя ``iblockId`` и поддерживая select/select_related."""

        filter_dict["iblockId"] = self.BITRIX_OBJECT_CLASS.IBLOCK_ID
        return super().filter(
            filter_dict=filter_dict,
            order_dict=order_dict,
            select_list=select_list,
            select_only=select_only,
            select_related=select_related,
            timeout=timeout,
        )

    def from_ids(self,
                 product_ids: Iterable[int],
                 order_dict: Optional[Dict] = None,
                 select_list: Optional[Iterable] = SELECT_FIELDS,
                 select_only: Optional[List[Text]] = None,
                 select_related: Optional[List[Text]] = None,
                 timeout: Optional[int] = None) -> BitrixObjectList["BITRIX_OBJECT_CLASS"]:
        """Получает товары по списку ID с теми же опциями выборки, что и ``filter``."""
        return super().from_ids(
            catalog_ids=product_ids,
            order_dict=order_dict,
            select_list=select_list,
            select_only=select_only,
            select_related=select_related,
            timeout=timeout,
        )

    def by_section(self, section_id: Optional[int], **kwargs) -> BitrixObjectList["BITRIX_OBJECT_CLASS"]:
        """Выбирает товары по ID раздела (включая ``None`` для корневых)."""
        filter_dict = {"iblockSectionId": section_id}
        return self.filter(filter_dict, **kwargs)

    def by_root_section(self, **kwargs) -> BitrixObjectList["BITRIX_OBJECT_CLASS"]:
        """Выбирает товары из корневых разделов."""
        return self.by_section(None, **kwargs)

    @property
    def _fields_method(self) -> Text:
        return f"catalog.{self.entity_type}.getFieldsByFilter"

    @staticmethod
    def _validate_api_fields(api_data: Dict) -> Dict:
        return api_data["product"]

    @staticmethod
    def _validate_api_add(api_data: Dict) -> Dict:
        return api_data["element"]["id"]

    @staticmethod
    def _validate_api_list(api_data: Dict) -> List:
        return api_data["products"]
