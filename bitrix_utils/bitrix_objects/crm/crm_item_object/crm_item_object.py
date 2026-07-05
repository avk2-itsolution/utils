from django.utils.functional import classproperty

from utils.bitrix_utils.bitrix_objects.crm.crm_item_object.crm_item_object_manager import CRMItemObjectManager
from utils.bitrix_utils.bitrix_objects.crm.crm_object import CRMObject

from utils.bitrix_utils.bitrix_objects.main.fields.bitrix_fields import (
    TextBitrixField,
    IntBitrixField,
    FloatBitrixField,
    DateBitrixField,
    DateTimeBitrixField,
    BoolBitrixField,
    ObjectBitrixField,
)

from typing import Dict, Text, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from utils.bitrix_utils.bitrix_objects.crm import StatusObject


class CRMItemObject(CRMObject):
    """Базовый класс смарт-процесса (требует указания ENTITY_TYPE_ID/ABBR у наследника).

    Обязательные параметры для ``crm.item.*`` через родительский менеджер:
    - entityTypeId: ID смарт-процесса.
    - fields: набор полей элемента.
    """

    ID_FIELD_CODE = "id"

    CONTACT_OBJECT = "utils.bitrix_utils.bitrix_objects.crm.base_contact_object.BaseContactObject"
    COMPANY_OBJECT = "utils.bitrix_utils.bitrix_objects.crm.base_company_object.BaseCompanyObject"
    USER_OBJECT = "utils.bitrix_utils.bitrix_objects.users.BaseUserObject"
    CATEGORY_OBJECT = "utils.bitrix_utils.bitrix_objects.crm.BaseCategoryObject"

    title = TextBitrixField("title")
    entity_type_id = IntBitrixField("entityTypeId", is_required=True)
    category = ObjectBitrixField("categoryId", object_type=CATEGORY_OBJECT, is_required=True)
    created_time = DateTimeBitrixField("createdTime", is_required=True)
    updated_time = DateTimeBitrixField("updatedTime", is_required=True)
    moved_time = DateTimeBitrixField("movedTime", is_required=True)
    created_by = ObjectBitrixField("createdBy", object_type=USER_OBJECT, is_required=True)
    updated_by = ObjectBitrixField("updatedBy", object_type=USER_OBJECT, is_required=True)
    moved_by = ObjectBitrixField("movedBy", object_type=USER_OBJECT, is_required=True)
    assigned_by = ObjectBitrixField("assignedById", object_type=USER_OBJECT, is_required=True)
    last_activity_time = DateTimeBitrixField("lastActivityTime")
    last_activity_by = ObjectBitrixField("lastActivityBy", object_type=USER_OBJECT)
    opened = BoolBitrixField("opened", is_required=True)
    source_id = TextBitrixField("sourceId")
    source_description = TextBitrixField("sourceDescription")
    stage_id = TextBitrixField("stageId")
    previous_stage_id = TextBitrixField("previousStageId")
    begin_date = DateBitrixField("begindate")
    close_date = DateBitrixField("closedate")
    contact = ObjectBitrixField("contactId", object_type=CONTACT_OBJECT)
    company = ObjectBitrixField("companyId", object_type=COMPANY_OBJECT)
    contacts = ObjectBitrixField("contactIds", object_type=CONTACT_OBJECT, is_multiple=True)
    observers = ObjectBitrixField("observers", object_type=USER_OBJECT, is_multiple=True)
    opportunity = FloatBitrixField("opportunity", is_required=True)
    is_manual_opportunity = BoolBitrixField("isManualOpportunity", is_required=True)
    opportunity_account = IntBitrixField("opportunityAccountId")
    tax_value = FloatBitrixField("taxValue", is_required=True)
    tax_value_account = IntBitrixField("taxValueAccount")
    account_currency_id = TextBitrixField("accountCurrencyId")
    my_company = ObjectBitrixField("mycompanyId", object_type=COMPANY_OBJECT)
    currency_id = TextBitrixField("currencyId")
    xml_id = TextBitrixField("xmlId")
    webform_id = IntBitrixField("webformId")
    utm_source = TextBitrixField("utmSource")
    utm_medium = TextBitrixField("urmMedium")
    utm_campaign = TextBitrixField("utmCampaign")
    utm_content = TextBitrixField("utmContent")
    utm_term = TextBitrixField("utmTerm")

    _objects = CRMItemObjectManager

    def __str__(self):
        return self.title.value

    @staticmethod
    def _validate_api_get(api_data: Dict) -> Dict:
        return api_data["item"]

    @classproperty
    def entity_type(cls) -> Text:
        """Тип CRM-сущности"""
        return "item"

    @property
    def url(self) -> Text:
        """Ссылка на элемент смарт процесса"""
        return f"{self.portal_url}/crm/type/{self.ENTITY_TYPE_ID}/details/{self.bitrix_id}/"

    @property
    def source(self) -> Optional["StatusObject"]:
        """Объект источника (статус из справочника)"""

        from utils.bitrix_utils.bitrix_objects.crm import StatusObject

        if self.source_id.value:
            return StatusObject.objects(self.but).by_status_id(status_id=self.source_id.value)
        else:
            return None

    @property
    def stage(self) -> Optional["StatusObject"]:
        """Объект стадии (статус из справочника)"""

        from utils.bitrix_utils.bitrix_objects.crm import StatusObject

        if self.stage_id.value:
            return StatusObject.objects(self.but).by_status_id(status_id=self.stage_id.value)
        else:
            return None

    @property
    def previous_stage(self) -> Optional["StatusObject"]:
        """Объект предыдущей стадии (статус из справочника)"""

        from utils.bitrix_utils.bitrix_objects.crm import StatusObject

        if self.previous_stage_id.value:
            return StatusObject.objects(self.but).by_status_id(status_id=self.previous_stage_id.value)
        else:
            return None

    def move_to_stage(self, stage_id: Text):
        """Передвинуть элемент смарт-процесса на конкретную стадию"""
        self.stage_id.value = stage_id
        self.save(update_fields=["stage_id"])

    @staticmethod
    def get_entity_type_abbr(entity_type_id: int) -> Text:
        return f"T{hex(entity_type_id).removeprefix('0x')}"

    @staticmethod
    def get_entity_type_name(entity_type_id: int) -> Text:
        return f"DYNAMIC_{entity_type_id}"
