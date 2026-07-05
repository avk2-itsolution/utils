from utils.bitrix_utils.bitrix_objects.crm.crm_sale_object.crm_sale_object_manager import CRMSaleObjectManager
from utils.bitrix_utils.bitrix_objects.crm.base_contact_object.contact_binding_interface import ContactBindingInterface
from utils.bitrix_utils.bitrix_objects.crm.crm_object import CRMObject
from utils.bitrix_utils.bitrix_objects.main.fields.bitrix_fields import (
    TextBitrixField,
    DateTimeBitrixField,
    FloatBitrixField,
    BoolBitrixField,
    ObjectBitrixField,
)

from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from utils.bitrix_utils.bitrix_objects.crm import StatusObject


class CRMSaleObject(CRMObject, ContactBindingInterface):
    """Объект сущности продажи (лид или сделка)"""

    FAILED = 'F'
    SUCCESS = 'S'
    PROCESSING = 'P'

    CONTACT_OBJECT = "utils.bitrix_utils.bitrix_objects.crm.BaseContactObject"
    COMPANY_OBJECT = "utils.bitrix_utils.bitrix_objects.crm.BaseCompanyObject"
    USER_OBJECT = "utils.bitrix_utils.bitrix_objects.users.BaseUserObject"

    _objects = CRMSaleObjectManager

    title = TextBitrixField("TITLE", is_required=True)
    currency_id = TextBitrixField("CURRENCY_ID")
    opportunity = FloatBitrixField("OPPORTUNITY")
    is_manual_opportunity = BoolBitrixField("IS_MANUAL_OPPORTUNITY", is_required=True)
    company = ObjectBitrixField("COMPANY_ID", object_type=COMPANY_OBJECT)
    contact = ObjectBitrixField("CONTACT_ID", object_type=CONTACT_OBJECT)
    assigned_by = ObjectBitrixField("ASSIGNED_BY_ID", object_type=USER_OBJECT, is_required=True)
    created_by = ObjectBitrixField("CREATED_BY_ID", object_type=USER_OBJECT, is_required=True)
    modify_by = ObjectBitrixField("MODIFY_BY_ID", object_type=USER_OBJECT, is_required=True)
    date_create = DateTimeBitrixField("DATE_CREATE", is_required=True)
    date_modify = DateTimeBitrixField("DATE_MODIFY", is_required=True)
    moved_by = ObjectBitrixField("MOVED_BY_ID", object_type=USER_OBJECT)
    moved_time = DateTimeBitrixField("MOVED_TIME")
    opened = BoolBitrixField("OPENED")
    comments = TextBitrixField("COMMENTS")
    source_id = TextBitrixField("SOURCE_ID")
    source_description = TextBitrixField("SOURCE_DESCRIPTION")
    originator_id = TextBitrixField("ORIGINATOR_ID")
    origin_id = TextBitrixField("ORIGIN_ID")
    last_activity_time = DateTimeBitrixField("LAST_ACTIVITY_TIME")
    last_activity_by = ObjectBitrixField("LAST_ACTIVITY_BY", object_type=USER_OBJECT)

    def __str__(self):
        return self.title.value

    @property
    def source(self) -> Optional["StatusObject"]:
        """Объект источника (статус из справочника)"""

        from utils.bitrix_utils.bitrix_objects.crm import StatusObject

        if self.source_id.value:
            return StatusObject.objects(self.but).by_status_id(status_id=self.source_id.value, entity_id="SOURCE")
        else:
            return None
