from utils.bitrix_utils.bitrix_objects.catalog.base_product_object.base_product_object_manager import BaseProductObjectManager
from utils.bitrix_utils.bitrix_objects.catalog.catalog_object import CatalogObject
from utils.bitrix_utils.bitrix_objects.main.fields import (
    BitrixField,
    TextBitrixField,
    IntBitrixField,
    FloatBitrixField,
    BoolBitrixField,
    BoolCharBitrixField,
    DateTimeBitrixField,
    FileBitrixField,
    ObjectBitrixField,
)

from typing import Dict, Any, Text


class BaseProductObject(CatalogObject):
    """Товар каталога (``PRODUCT``) с полями инфоблока и торговыми параметрами.

    Требует задания ``IBLOCK_ID`` у потомков и подставляет его в запросы
    менеджера. Использует типовые поля товаров (активность, описание, цены,
    изображения, принадлежность к разделам).

    Examples:
        Наследование для конкретного инфоблока:
            class Product(BaseProductObject):
                IBLOCK_ID = 10

        Работа с товаром:
            >>> product = Product.objects(but).get(bitrix_id=123)
            >>> product.name.value
            >>> product.get_field_value(product.vat_id)
            >>> product.url()
    """

    IBLOCK_ID: int = NotImplementedError

    ENTITY_TYPE_NAME = "PRODUCT"

    CATALOG_OBJECT = "utils.bitrix_utils.bitrix_objects.catalog.BaseCatalogObject"
    SECTION_OBJECT = "utils.bitrix_utils.bitrix_objects.catalog.BaseSectionObject"
    MEASURE_OBJECT = "utils.bitrix_utils.bitrix_objects.measure.BaseMeasureObject"
    USER_OBJECT = "utils.bitrix_utils.bitrix_objects.users.BaseUserObject"

    _objects = BaseProductObjectManager

    iblock = ObjectBitrixField("iblockId", object_type=CATALOG_OBJECT, is_required=True)
    name = TextBitrixField("name", is_required=True)
    active = BoolBitrixField("active", is_required=True)
    available = BoolBitrixField("available", is_required=True)
    code = TextBitrixField("code")
    xml_id = TextBitrixField("xmlId")
    barcode_multi = BoolBitrixField("barcodeMulti", is_required=True)
    bundle = BoolBitrixField("bundle", is_required=True)
    can_buy_zero = BoolBitrixField("canBuyZero", is_required=True)
    created_by = ObjectBitrixField("createdBy", object_type=USER_OBJECT, is_required=True)
    modified_by = ObjectBitrixField("modifiedBy", object_type=USER_OBJECT, is_required=True)
    date_active_from = DateTimeBitrixField("dateActiveFrom")
    dateActiveTo = DateTimeBitrixField("dateActiveTo")
    date_create = DateTimeBitrixField("dateCreate", is_required=True)
    timestamp_x = DateTimeBitrixField("timestampX", is_required=True)
    iblock_section_id = ObjectBitrixField("iblockSectionId", object_type=SECTION_OBJECT)
    iblock_section_ids = ObjectBitrixField("iblockSection", object_type=SECTION_OBJECT, is_multiple=True)
    measure = ObjectBitrixField("measure", object_type=MEASURE_OBJECT)
    preview_text = TextBitrixField("previewText")
    detail_text = TextBitrixField("detailText")
    preview_picture = FileBitrixField("previewPicture", is_crm_entity=True)
    detail_picture = FileBitrixField("detailPicture", is_crm_entity=True)
    preview_text_type = TextBitrixField("previewTextType", is_required=True)
    detail_text_type = TextBitrixField("detailTextType", is_required=True)
    sort = IntBitrixField("sort")
    subscribe = BoolCharBitrixField("subscribe", is_required=True)
    vat_id = IntBitrixField("vatId")
    vatIncluded = BoolBitrixField("vatIncluded")
    height = FloatBitrixField("height")
    length = FloatBitrixField("length")
    weight = FloatBitrixField("weight")
    width = FloatBitrixField("width")
    quantity_trace = BoolCharBitrixField("quantityTrace", is_required=True)
    purchasing_currency = TextBitrixField("purchasingCurrency")
    purchasing_price = FloatBitrixField("purchasingPrice")
    quantity = FloatBitrixField("quantity")
    quantity_reserved = FloatBitrixField("quantityReserved")
    recur_scheme_length = IntBitrixField("recurSchemeLength")
    recur_scheme_type = TextBitrixField("recurSchemeType")
    trial_price_id = IntBitrixField("trialPriceId")
    without_order = BoolBitrixField("withoutOrder", is_required=True)

    def __str__(self):
        return self.name.value

    def get_field_value(self, bitrix_field: BitrixField) -> Any:
        """Возвращает значение поля, разворачивая вложенные ``{"value": ...}`` и множественные списки."""
        value = super().get_field_value(bitrix_field)

        if value and (isinstance(value, dict) or (isinstance(value, list) and isinstance(value[0], dict))):
            # если пользовательское поле
            if bitrix_field.is_multiple:
                return [data["value"] for data in value]
            else:
                return value["value"]

        return value

    @staticmethod
    def _validate_api_get(api_data: Dict) -> Dict:
        """Извлекает данные товара из ответа REST."""
        return api_data["product"]

    def url(self) -> Text:
        """Возвращает URL карточки товара в портале."""
        return f"{self.iblock.object.url}/product/{self.bitrix_id}/"
