from utils.bitrix_utils.bitrix_objects.catalog.base_catalog_object.base_catalog_object_manager import BaseCatalogObjectManager
from utils.bitrix_utils.bitrix_objects.catalog.catalog_object import CatalogObject
from utils.bitrix_utils.bitrix_objects.main.fields import (
    TextBitrixField,
    IntBitrixField,
    BoolBitrixField,
)

from typing import Dict, Text


class BaseCatalogObject(CatalogObject):
    """Инфоблок торгового каталога (``CATALOG``) и его поля Bitrix24.

    Содержит идентификаторы связанных инфоблоков, настройки экспортов и флаг
    офферного каталога. CRUD выполняется через ``catalog.catalog.*``.

    Examples:
        >>> catalog = BaseCatalogObject.objects(but).get(bitrix_id=5)
        >>> catalog.is_offers()
        >>> catalog.url()
    """

    ENTITY_TYPE_NAME = "CATALOG"

    _objects = BaseCatalogObjectManager

    iblock_id = IntBitrixField("iblockId", is_required=True)
    iblock_typeId = TextBitrixField("iblockTypeId", is_required=True)
    lid = TextBitrixField("lid", is_required=True)
    name = TextBitrixField("name", is_required=True)
    product_iblock_id = IntBitrixField("productIblockId")
    sku_property_id = IntBitrixField("skuPropertyId")
    subscription = BoolBitrixField("subscription", is_required=True)
    vat_id = IntBitrixField("vatId", is_required=True)
    yandex_export = BoolBitrixField("yandexExport", is_required=True)

    def __str__(self):
        return self.name.value

    def is_offers(self) -> bool:
        """Возвращает ``True``, если каталог офферный (SKU)."""
        return self.but.call_api_method("catalog.catalog.isOffers")["result"]

    @staticmethod
    def _validate_api_get(api_data: Dict) -> Dict:
        return api_data["catalog"]

    def url(self) -> Text:
        """Возвращает URL страницы каталога в портале."""
        return f"{self.portal_url}/crm/catalog/{self.bitrix_id}/"
