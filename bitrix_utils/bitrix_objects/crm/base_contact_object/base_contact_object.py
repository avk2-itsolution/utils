from utils.bitrix_utils.bitrix_objects.crm.base_contact_object.base_contact_object_manager import BaseContactObjectManager
from utils.bitrix_utils.bitrix_objects.crm.base_company_object.company_binding_interface import CompanyBindingInterface
from utils.bitrix_utils.bitrix_objects.crm.crm_object import CRMObject
from utils.bitrix_utils.bitrix_objects.main.fields import (
    TextBitrixField,
    IntBitrixField,
    DateBitrixField,
    DateTimeBitrixField,
    BoolBitrixField,
    ObjectBitrixField,
    FileBitrixField,
    MultiBitrixField,
)

from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from utils.bitrix_utils.bitrix_objects.crm import StatusObject


class BaseContactObject(CRMObject, CompanyBindingInterface):
    """Контакт CRM (готовый класс).

    Examples:
        >>> contact = BaseContactObject.objects(but).get(bitrix_id=301)
        >>> contact.phone.value
        >>> contact.save(update_fields=["last_name"])
    """

    ENTITY_TYPE_ID = 3
    ENTITY_TYPE_NAME = "CONTACT"
    ENTITY_TYPE_ABBR = "C"
    USER_FIELD_ENTITY_ID = "CRM_CONTACT"

    LEAD_OBJECT = "utils.bitrix_utils.bitrix_objects.crm.base_lead_object.BaseLeadObject"
    COMPANY_OBJECT = "utils.bitrix_utils.bitrix_objects.crm.base_company_object.BaseCompanyObject"
    USER_OBJECT = "utils.bitrix_utils.bitrix_objects.users.BaseUserObject"

    _objects = BaseContactObjectManager

    name = TextBitrixField("NAME")
    second_name = TextBitrixField("SECOND_NAME")
    last_name = TextBitrixField("LAST_NAME")
    post = TextBitrixField("POST")
    comments = TextBitrixField("COMMENST")
    honorific = TextBitrixField("HONORIFIC")
    photo = FileBitrixField("PHOTO", is_crm_entity=True)
    lead = ObjectBitrixField("LEAD_ID", object_type=LEAD_OBJECT)
    type_id = TextBitrixField("TYPE_ID")
    source_id = TextBitrixField("SOURCE_ID")
    source_description = TextBitrixField("SOURCE_DESCRIPTION")
    company = ObjectBitrixField("COMPANY_ID", object_type=COMPANY_OBJECT)
    birthdate = DateBitrixField("BIRTHDATE")
    export = BoolBitrixField("EXPORT", is_required=True)
    has_phone = BoolBitrixField("HAS_PHONE", is_required=True)
    has_email = BoolBitrixField("HAS_EMAIL", is_required=True)
    has_imol = BoolBitrixField("HAS_IMOL", is_required=True)
    date_create = DateTimeBitrixField("DATE_CREATE", is_required=True)
    date_modify = DateTimeBitrixField("DATE_MODIFY", is_required=True)
    assigned_by = ObjectBitrixField("ASSIGNED_BY_ID", object_type=USER_OBJECT, is_required=True)
    created_by = ObjectBitrixField("CREATED_BY_ID", object_type=USER_OBJECT, is_required=True)
    modify_by = ObjectBitrixField("MODIFY_BY_ID", object_type=USER_OBJECT, is_required=True)
    opened = BoolBitrixField("OPENED", is_required=True)
    originator_id = TextBitrixField("ORIGINATOR_ID")
    origin_id = TextBitrixField("ORIGIN_ID")
    origin_version = TextBitrixField("ORIGIN_VERSION")
    face_id = IntBitrixField("FACE_ID")
    last_activity_time = DateTimeBitrixField("LAST_ACTIVITY_TIME")
    last_activity_by = ObjectBitrixField("LAST_ACTIVITY_BY", object_type=USER_OBJECT)
    address = TextBitrixField("ADDRESS")
    address_2 = TextBitrixField("ADDRESS_2")
    address_city = TextBitrixField("ADDRESS_CITY")
    address_postal_code = TextBitrixField("ADDRESS_POSTAL_CODE")
    address_region = TextBitrixField("ADDRESS_REGION")
    address_province = TextBitrixField("ADDRESS_PROVINCE")
    address_country = TextBitrixField("ADDRESS_COUNTRY")
    address_loc_addr_id = IntBitrixField("ADDRESS_LOC_ADDR_ID")
    utm_source = TextBitrixField("UTM_SOURCE")
    utm_medium = TextBitrixField("UTM_MEDIUM")
    utm_campaign = TextBitrixField("UTM_CAMPAIGN")
    utm_content = TextBitrixField("UTM_CONTENT")
    utm_term = TextBitrixField("UTM_TERM")
    phone = MultiBitrixField("PHONE")
    email = MultiBitrixField("EMAIL")
    web = MultiBitrixField("WEB")
    im = MultiBitrixField("IM")
    link = MultiBitrixField("LINK")

    def __str__(self):
        last_name = self.last_name.value or ""
        name = self.name.value or ""
        second_name = self.second_name.value or ""
        return f"{last_name} {name} {second_name}".strip()

    @property
    def honorific_object(self) -> Optional["StatusObject"]:
        """Объект вида обращения (статус из справочника)"""

        from utils.bitrix_utils.bitrix_objects.crm import StatusObject

        if self.honorific.value:
            return StatusObject.objects(self.but).by_status_id(status_id=self.honorific.value, entity_id="HONORIFIC")
        else:
            return None

    @property
    def type(self) -> Optional["StatusObject"]:
        """Объект типа контакта (статус из справочника)"""

        from utils.bitrix_utils.bitrix_objects.crm import StatusObject

        if self.type_id.value:
            return StatusObject.objects(self.but).by_status_id(status_id=self.type_id.value, entity_id="CONTACT_TYPE")
        else:
            return None

    @property
    def source(self) -> Optional["StatusObject"]:
        """Объект источника (статус из справочника)"""

        from utils.bitrix_utils.bitrix_objects.crm import StatusObject

        if self.source_id.value:
            return StatusObject.objects(self.but).by_status_id(status_id=self.source_id.value, entity_id="SOURCE")
        else:
            return None
