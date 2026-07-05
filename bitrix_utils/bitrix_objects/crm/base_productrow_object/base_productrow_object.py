from utils.bitrix_utils.bitrix_objects.crm.base_productrow_object.base_productrow_object_manager import BaseProductRowObjectManager
from utils.bitrix_utils.bitrix_objects.crm.crm_object.crm_object import CRMObject
from utils.bitrix_utils.bitrix_objects.main.fields import (
    TextBitrixField,
    BoolBitrixField,
    IntBitrixField,
    FloatBitrixField,
    ObjectBitrixField,
)


from typing import Dict


class BaseProductRowObject(CRMObject):
    """Товарная позиция CRM (готовый класс).

    Examples:
        >>> rows = BaseProductRowObject.objects(but).get_by_item(owner_id=501, owner_type="D")
        >>> rows[0].price.value
    """

    ENTITY_TYPE_NAME = "ITEM.PRODUCTROW"
    USER_FIELD_ENTITY_ID = "CRM_ITEM_PRODUCT_ROW"

    ID_FIELD_CODE = "id"

    ABSULUTE_DISCOUNT_TYPE = 1
    PERCENTAGE_DISCOUNT_TYPE = 2

    SIMPLE_PRODUCT_TYPE = 1
    SET_TYPE = 2
    PRODUCT_WITH_TRADE_OFFER_TYPE = 3
    TRADE_OFFER_TYPE = 4
    TRADE_OFFER_WITHOUNT_PRODUCT_TYPE = 5
    SPECIFIC_TYPE = 6
    SERVICE_TYPE = 7

    PRODUCT_OBJECT = "utils.bitrix_utils.bitrix_objects.catalog.BaseProductObject"

    _objects = BaseProductRowObjectManager

    owner_id = IntBitrixField("ownerId", is_required=True)
    owner_type = TextBitrixField("ownerType", is_required=True)
    product = ObjectBitrixField("productId", object_type=PRODUCT_OBJECT, is_required=True)
    product_name = TextBitrixField("productName", is_required=True)
    price = FloatBitrixField("price", is_required=True)
    price_account = FloatBitrixField("priceAccount", is_required=True)
    price_exclusive = FloatBitrixField("priceExclusive", is_required=True)
    price_netto = FloatBitrixField("priceNetto", is_required=True)
    price_brutto = FloatBitrixField("priceBrutto", is_required=True)
    quantity = FloatBitrixField("quantity", is_required=True)
    discount_type_id = IntBitrixField("discountTypeId", is_required=True)
    discount_rate = FloatBitrixField("discountRate", is_required=True)
    discount_sum = FloatBitrixField("discountSum", is_required=True)
    tax_rate = FloatBitrixField("taxRate")
    tax_included = BoolBitrixField("taxIncluded", is_required=True)
    customized = BoolBitrixField("customized", is_required=True)
    measure_code = IntBitrixField("measureCode", is_required=True)
    measure_name = TextBitrixField("measureName", is_required=True)
    sort = IntBitrixField("sort", is_required=True)
    type = IntBitrixField("type", is_required=True)
    xml_id = TextBitrixField("xmlId")

    def __str__(self):
        return self.product_name.value

    @staticmethod
    def _validate_api_get(api_data: Dict) -> Dict:
        return api_data["productRow"]
