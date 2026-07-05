from utils.bitrix_utils.bitrix_objects.catalog.base_section_object.base_section_object_manager import BaseSectionObjectManager
from utils.bitrix_utils.bitrix_objects.catalog.catalog_object import CatalogObject
from utils.bitrix_utils.bitrix_objects.main.bitrix_object_list import BitrixObjectList
from utils.bitrix_utils.bitrix_objects.main.fields import (
    TextBitrixField,
    IntBitrixField,
    BoolBitrixField,
    ObjectBitrixField,
)

from typing import Dict


class BaseSectionObject(CatalogObject):
    """Раздел торгового каталога (``SECTION``) с привязкой к инфоблоку.

    Требует задания ``IBLOCK_ID`` у потомков и хранит связи с родительским
    разделом, каталогом и товарами.

    Examples:
        Наследование под конкретный инфоблок:
            class Section(BaseSectionObject):
                IBLOCK_ID = 7

        Получение товаров раздела:
            >>> section = Section.objects(but).get(bitrix_id=42)
            >>> section.is_root_section
            >>> section.get_products()
    """

    IBLOCK_ID: int = NotImplementedError

    ENTITY_TYPE_NAME = "SECTION"

    CATALOG_OBJECT = "utils.bitrix_utils.bitrix_objects.catalog.BaseCatalogObject"
    SECTION_OBJECT = "utils.bitrix_utils.bitrix_objects.catalog.BaseSectionObject"
    PRODUCT_OBJECT = "utils.bitrix_utils.bitrix_objects.catalog.BaseProductObject"

    _objects = BaseSectionObjectManager

    iblock = ObjectBitrixField("iblockId", object_type=CATALOG_OBJECT, is_required=True)
    name = TextBitrixField("name", is_required=True)
    iblock_section = ObjectBitrixField("iblockSectionId", object_type=SECTION_OBJECT)
    xml_id = TextBitrixField("xmlId")
    code = TextBitrixField("code")
    sort = IntBitrixField("sort")
    active = BoolBitrixField("active", is_required=True)
    description = TextBitrixField("description")
    description_type = TextBitrixField("descriptionType")

    def __str__(self):
        return self.name.value

    @property
    def is_root_section(self) -> bool:
        """Возвращает ``True``, если отсутствует родительский раздел."""
        return self.iblock_section.value is None

    def get_products(self, **kwargs) -> BitrixObjectList["PRODUCT_OBJECT"]:
        """Возвращает товары, привязанные к текущему разделу."""
        product_class = self.get_class(self.PRODUCT_OBJECT)
        return product_class.objects(self.but).by_section(self.bitrix_id, **kwargs)

    @staticmethod
    def _validate_api_get(api_data: Dict) -> Dict:
        """Извлекает данные раздела из ответа REST."""
        return api_data["section"]
