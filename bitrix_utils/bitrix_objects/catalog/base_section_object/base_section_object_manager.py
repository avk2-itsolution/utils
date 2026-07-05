from utils.bitrix_utils.bitrix_objects.catalog.catalog_object.catalog_object_manager import CatalogObjectManager
from utils.bitrix_utils.bitrix_objects.main.bitrix_object_list import BitrixObjectList

from typing import Type, TYPE_CHECKING, Dict, List, Optional, Text, Iterable

if TYPE_CHECKING:
    from utils.bitrix_utils.bitrix_objects.catalog import BaseSectionObject


class BaseSectionObjectManager(CatalogObjectManager):
    """Менеджер разделов с автоподстановкой ``IBLOCK_ID`` и выборками по иерархии.

    Examples:
        >>> sections = Section.objects(but).root_sections()
        >>> nested = Section.objects(but).nested_sections(section_id=10)
    """

    BITRIX_OBJECT_CLASS: Type["BaseSectionObject"]

    def filter(self,
               filter_dict: Dict,
               order_dict: Optional[Dict] = None,
               select_list: Optional[Iterable] = None,
               select_only: Optional[List[Text]] = None,
               select_related: Optional[List[Text]] = None,
               timeout: Optional[int] = None) -> BitrixObjectList["BITRIX_OBJECT_CLASS"]:
        """Возвращает разделы по фильтру, автоматически добавляя ``iblockId``.

        Обязательные параметры ``catalog.section.list``:
        - filter.iblockId: ID инфоблока (``IBLOCK_ID`` класса).
        """

        filter_dict["iblockId"] = self.BITRIX_OBJECT_CLASS.IBLOCK_ID
        return super().filter(
            filter_dict=filter_dict,
            order_dict=order_dict,
            select_list=select_list,
            select_only=select_only,
            select_related=select_related,
            timeout=timeout,
        )

    def nested_sections(self, section_id: Optional[int], **kwargs) -> BitrixObjectList["BITRIX_OBJECT_CLASS"]:
        """Возвращает дочерние разделы по ID родителя (или ``None``)."""
        filter_dict = {"iblockSectionId": section_id}
        return self.filter(filter_dict, **kwargs)

    def root_sections(self, **kwargs) -> BitrixObjectList["BITRIX_OBJECT_CLASS"]:
        """Возвращает корневые разделы (без родителя)."""
        return self.nested_sections(None, **kwargs)

    @staticmethod
    def _validate_api_fields(api_data: Dict) -> Dict:
        return api_data["section"]

    @staticmethod
    def _validate_api_add(api_data: Dict) -> Dict:
        return api_data["section"]["id"]

    @staticmethod
    def _validate_api_list(api_data: Dict) -> List:
        return api_data["sections"]
