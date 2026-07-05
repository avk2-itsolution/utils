from utils.bitrix_utils.bitrix_objects.crm.base_invoice_object.base_invoice_object_manager import BaseInvoiceObjectManager
from utils.bitrix_utils.bitrix_objects.crm import CRMItemObject
from utils.bitrix_utils.bitrix_objects.main.fields.bitrix_fields import TextBitrixField


class BaseInvoiceObject(CRMItemObject):
    """Базовый класс для счета"""

    ENTITY_TYPE_ID = 31
    ENTITY_TYPE_NAME = "SMART_INVOICE"
    ENTITY_TYPE_ABBR = "SI"
    USER_FIELD_ENTITY_ID = "CRM_SMART_INVOICE"

    _objects = BaseInvoiceObjectManager

    comments = TextBitrixField("comments")
    account_number = TextBitrixField("accountNumber")
    location_id = TextBitrixField("locationId")
