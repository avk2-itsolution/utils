from utils.bitrix_utils.bitrix_objects.crm.vat_object.vat_object_manager import VATObjectManager
from utils.bitrix_utils.bitrix_objects.crm.crm_object import CRMObject
from utils.bitrix_utils.bitrix_objects.main.fields import (
    TextBitrixField,
    IntBitrixField,
    DateTimeBitrixField,
    BoolBitrixField,
    FloatBitrixField,
)


class VATObject(CRMObject):
    """Ставка НДС CRM (готовый класс).

    Examples:
        >>> vats = VATObject.objects(but).all()
    """

    ENTITY_TYPE_NAME = "VAT"
    USER_FIELD_ENTITY_ID = "CRM_VAT"

    _objects = VATObjectManager

    name = TextBitrixField("NAME", is_required=True)
    timestamp_x = DateTimeBitrixField("TIMESTAMP_X", is_required=True)
    active = BoolBitrixField("ACTIVE", is_required=True)
    rate = FloatBitrixField("RATE", is_required=True)
    c_sort = IntBitrixField("C_SORT", is_required=True)

    def __str__(self):
        return self.name.value
