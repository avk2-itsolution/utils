from utils.bitrix_utils.bitrix_objects.crm.base_lead_object.base_lead_object_manager import BaseLeadObjectManager
from utils.bitrix_utils.bitrix_objects.crm.crm_sale_object import CRMSaleObject
from utils.bitrix_utils.bitrix_objects.main.bitrix_object_list import BitrixObjectList
from utils.bitrix_utils.bitrix_objects.main.fields.bitrix_fields import (
    TextBitrixField,
    IntBitrixField,
    DateBitrixField,
    DateTimeBitrixField,
    BoolBitrixField,
    MultiBitrixField,
)

from typing import Optional, TYPE_CHECKING, Text

if TYPE_CHECKING:
    from utils.bitrix_utils.bitrix_objects.crm import StatusObject


class BaseLeadObject(CRMSaleObject):
    """Лид CRM (готовый к использованию класс).

    Examples:
        >>> lead = BaseLeadObject.objects(but).get(bitrix_id=101)
        >>> lead.title.value
        >>> lead.honorific_object
    """

    ENTITY_TYPE_ID = 1
    ENTITY_TYPE_NAME = "LEAD"
    ENTITY_TYPE_ABBR = "L"
    USER_FIELD_ENTITY_ID = "CRM_LEAD"

    JUNK_STATUS = "JUNK"
    CONVERTED_STATUS = "CONVERTED"

    # Статусы (стадии) лида
    _statuses: Optional[BitrixObjectList["StatusObject"]] = None

    _objects = BaseLeadObjectManager

    title = TextBitrixField("TITLE", is_required=True)
    name = TextBitrixField("NAME")
    honorific = TextBitrixField("HONORIFIC")
    second_name = TextBitrixField("SECOND_NAME")
    last_name = TextBitrixField("LAST_NAME")
    birthdate = DateBitrixField("BIRTHDATE")
    company_title = TextBitrixField("COMPANY_TITLE")
    status_id = TextBitrixField("STATUS_ID")
    status_description = TextBitrixField("STATUS_DESCRIPTION")
    status_semantic_id = TextBitrixField("STATUS_SEMANTICID_ID", is_required=True)
    post = TextBitrixField("POST")
    address = TextBitrixField("ADDRESS")
    address_2 = TextBitrixField("ADDRESS_2")
    address_city = TextBitrixField("ADDRESS_CITY")
    address_postal_code = TextBitrixField("ADDRESS_POSTAL_CODE")
    address_region = TextBitrixField("ADDRESS_REGION")
    address_province = TextBitrixField("ADDRESS_PROVINCE")
    address_country = TextBitrixField("ADDRESS_COUNTRY")
    address_country_code = TextBitrixField("ADDRESS_COUNTRY_CODE")
    address_loc_addr_id = IntBitrixField("ADDRESS_LOC_ADDR_ID")
    has_phone = BoolBitrixField("HAS_PHONE")
    has_email = BoolBitrixField("HAS_EMAIL")
    has_imol = BoolBitrixField("HAS_IMOL")
    is_returned_customer = BoolBitrixField("IS_RETURNED_CUSTOMER", is_required=True)
    date_closed = DateTimeBitrixField("DATE_CLOSED")
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

    @property
    def honorific_object(self) -> Optional["StatusObject"]:
        """Объект вида обращения (статус из справочника)"""

        from utils.bitrix_utils.bitrix_objects.crm import StatusObject

        if self.honorific.value:
            return StatusObject.objects(self.but).by_status_id(status_id=self.honorific.value, entity_id="HONORIFIC")
        else:
            return None

    @property
    def status(self) -> Optional["StatusObject"]:
        """Объект стадии лида (статус из справочника)"""

        from utils.bitrix_utils.bitrix_objects.crm import StatusObject

        if self.status_id.value:
            return StatusObject.objects(self.but).by_status_id(status_id=self.status_id.value, entity_id="STATUS")
        else:
            return None

    @property
    def statuses(self) -> BitrixObjectList["StatusObject"]:
        """Статусы (стадии) лида"""
        if self._statuses is None:
            self.__class__._statuses = self.objects(self.but).get_statuses()
        return self._statuses

    def move_to_status(self, status_id: Text):
        """Передвинуть лид на конкретную стадию (статус)"""
        self.status_id.value = status_id
        self.save(update_fields=["status_id"])

    def move_to_converted_status(self):
        """Передвинуть лид на стадию (статус) конвертации"""
        self.move_to_status(self.CONVERTED_STATUS)

    def move_to_junk_status(self):
        """Передвинуть лид на проигранную стадию (статус)"""
        self.move_to_status(self.JUNK_STATUS)
