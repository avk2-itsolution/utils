from utils.bitrix_utils.bitrix_objects.crm.base_company_object.base_company_object_manager import BaseCompanyObjectManager
from utils.bitrix_utils.bitrix_objects.crm.base_contact_object.contact_binding_interface import ContactBindingInterface
from utils.bitrix_utils.bitrix_objects.crm.crm_object import CRMObject
from utils.bitrix_utils.bitrix_objects.main.fields import (
    TextBitrixField,
    IntBitrixField,
    DateTimeBitrixField,
    FloatBitrixField,
    BoolBitrixField,
    ObjectBitrixField,
    FileBitrixField,
    MultiBitrixField,
)

from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from utils.bitrix_utils.bitrix_objects.crm import StatusObject


class BaseCompanyObject(CRMObject, ContactBindingInterface):
    """Компания CRM (готовый класс).

    Examples:
        >>> company = BaseCompanyObject.objects(but).get(bitrix_id=201)
        >>> company.phone.value
        >>> company.save(update_fields=["title"])
    """

    ENTITY_TYPE_ID = 4
    ENTITY_TYPE_NAME = "COMPANY"
    ENTITY_TYPE_ABBR = "CO"
    USER_FIELD_ENTITY_ID = "CRM_COMPANY"

    LEAD_OBJECT = "utils.bitrix_utils.bitrix_objects.crm.base_lead_object.BaseLeadObject"
    CONTACT_OBJECT = "utils.bitrix_utils.bitrix_objects.crm.base_contact_object.BaseContactObject"
    USER_OBJECT = "utils.bitrix_utils.bitrix_objects.users.BaseUserObject"

    _objects = BaseCompanyObjectManager

    title = TextBitrixField("TITLE", is_required=True)
    company_type = TextBitrixField("COMPANY_TYPE")
    logo = FileBitrixField("LOGO")
    lead = ObjectBitrixField("LEAD", object_type=LEAD_OBJECT)
    has_phone = BoolBitrixField("HAS_PHONE", is_required=True)
    has_email = BoolBitrixField("HAS_EMAIL", is_required=True)
    has_imol = BoolBitrixField("HAS_IMOL", is_required=True)
    assigned_by = ObjectBitrixField("ASSIGNED_BY_ID", object_type=USER_OBJECT, is_required=True)
    created_by = ObjectBitrixField("CREATED_BY_ID", object_type=USER_OBJECT, is_required=True)
    modify_by = ObjectBitrixField("MODIFY_BY_ID", object_type=USER_OBJECT, is_required=True)
    banking_details = TextBitrixField("BANKING_DETAILS")
    industry = TextBitrixField("INDUSTRY")
    revenue = FloatBitrixField("REVENUE")
    currency_id = TextBitrixField("CURRENCY_ID")
    employees = TextBitrixField("EMPLOYEES")
    comments = TextBitrixField("COMMENTS")
    date_create = DateTimeBitrixField("DATE_CREATE", is_required=True)
    date_modify = DateTimeBitrixField("DATE_MODIFY", is_required=True)
    opened = BoolBitrixField("OPENED", is_required=True)
    is_my_company = BoolBitrixField("IS_MY_COMPANY", is_required=True)
    originator_id = TextBitrixField("ORIGINATOR_ID")
    origin_id = TextBitrixField("ORIGIN_ID")
    origin_version = TextBitrixField("ORIGIN_VERSION")
    last_activity_time = DateTimeBitrixField("LAST_ACTIVITY_TIME")
    last_activity_by = ObjectBitrixField("LAST_ACTIVITY_BY", object_type=USER_OBJECT)
    address = TextBitrixField("ADDRESS")
    address_2 = TextBitrixField("ADDRESS_2")
    address_city = TextBitrixField("ADDRESS_CITY")
    address_postal_code = TextBitrixField("ADDRESS_POSTAL_CODE")
    address_region = TextBitrixField("ADDRESS_REGION")
    address_province = TextBitrixField("ADDRESS_PROVINCE")
    address_country = TextBitrixField("ADDRESS_COUNTRY")
    address_country_code = TextBitrixField("ADDRESS_COUNTRY_CODE")
    address_loc_addr_id = IntBitrixField("ADDRESS_LOC_ADDR_ID")
    address_legal = TextBitrixField("ADDRESS_LEGAL")
    reg_address = TextBitrixField("REG_ADDRESS")
    reg_address_2 = TextBitrixField("REG_ADDRESS_2")
    reg_address_city = TextBitrixField("REG_ADDRESS_CITY")
    reg_address_postal_code = TextBitrixField("REG_ADDRESS_POSTAL_CODE")
    reg_address_region = TextBitrixField("REG_ADDRESS_REGION")
    reg_address_province = TextBitrixField("REG_ADDRESS_PROVINCE")
    reg_address_country = TextBitrixField("REG_ADDRESS_COUNTRY")
    reg_address_country_code = TextBitrixField("REG_ADDRESS_COUNTRY_CODE")
    reg_address_loc_addr_id = IntBitrixField("REG_ADDRESS_LOC_ADDR_ID")
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
        return self.title.value

    @property
    def company_type_object(self) -> Optional["StatusObject"]:
        """Объект типа компании (статус из справочника)"""

        from utils.bitrix_utils.bitrix_objects.crm import StatusObject

        if self.company_type.value:
            return StatusObject.objects(self.but).by_status_id(status_id=self.company_type.value, entity_id="COMPANY_TYPE")
        else:
            return None

    @property
    def employees_object(self) -> Optional["StatusObject"]:
        """Объект количества сотрудников (статус из справочника)"""

        from utils.bitrix_utils.bitrix_objects.crm import StatusObject

        if self.employees.value:
            return StatusObject.objects(self.but).by_status_id(status_id=self.employees.value, entity_id="EMPLOYEES")
        else:
            return None

    @property
    def industry_object(self) -> Optional["StatusObject"]:
        """Объект сферы деятельности (статус из справочника)"""

        from utils.bitrix_utils.bitrix_objects.crm import StatusObject

        if self.industry.value:
            return StatusObject.objects(self.but).by_status_id(status_id=self.industry.value, entity_id="INDUSTRY")
        else:
            return None
