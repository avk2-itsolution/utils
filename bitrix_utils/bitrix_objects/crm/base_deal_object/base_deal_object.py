from utils.bitrix_utils.bitrix_objects.crm.base_deal_object.base_deal_object_manager import BaseDealObjectManager
from utils.bitrix_utils.bitrix_objects.crm.crm_sale_object import CRMSaleObject
from utils.bitrix_utils.bitrix_objects.main.fields import (
    TextBitrixField,
    IntBitrixField,
    DateBitrixField,
    FloatBitrixField,
    BoolBitrixField,
    ObjectBitrixField,
)

from typing import Optional, TYPE_CHECKING, Text

if TYPE_CHECKING:
    from utils.bitrix_utils.bitrix_objects.crm import StatusObject


class BaseDealObject(CRMSaleObject):
    """Сделка CRM (готовый класс).

    Examples:
        >>> deal = BaseDealObject.objects(but).get(bitrix_id=501)
        >>> deal.move_to_stage(deal.category.object.win_stage_status_id)
    """

    ENTITY_TYPE_ID = 2
    ENTITY_TYPE_NAME = "DEAL"
    ENTITY_TYPE_ABBR = "D"
    USER_FIELD_ENTITY_ID = "CRM_DEAL"

    LEAD_OBJECT = "utils.bitrix_utils.bitrix_objects.crm.BaseLeadObject"
    CATEGORY_OBJECT = "utils.bitrix_utils.bitrix_objects.crm.BaseDealCategoryObject"

    _objects = BaseDealObjectManager

    type_id = TextBitrixField("TYPE_ID")
    stage_id = TextBitrixField("STAGE_ID")
    probability = IntBitrixField("PROBABILITY")
    is_new = BoolBitrixField("IS_NEW", is_required=True)
    is_recurring = BoolBitrixField("IS_RECURRING", is_required=True)
    is_return_customer = BoolBitrixField("IS_RETURN_CUSTOMER", is_required=True)
    is_repeated_approach = BoolBitrixField("IS_REPEATED_APPROACH", is_required=True)
    tax_value = FloatBitrixField("TAX_VALUE")
    lead = ObjectBitrixField("LEAD_ID", object_type=LEAD_OBJECT)
    quote_id = IntBitrixField("QUOTE_ID")
    begindate = DateBitrixField("BEGINDATE")
    closedate = DateBitrixField("CLOSEDATE")
    closed = BoolBitrixField("CLOSED")
    additional_info = TextBitrixField("ADDITIONAL_INFO")
    location_id = IntBitrixField("LOCATION_ID")
    category = ObjectBitrixField("CATEGORY_ID", object_type=CATEGORY_OBJECT, is_required=True)
    stage_semantic_id = TextBitrixField("STAGE_SEMANTIC_ID", is_required=True)
    utm_source = TextBitrixField("UTM_SOURCE")
    utm_medium = TextBitrixField("UTM_MEDIUM")
    utm_campaign = TextBitrixField("UTM_CAMPAIGN")
    utm_content = TextBitrixField("UTM_CONTENT")
    utm_term = TextBitrixField("UTM_TERM")

    @property
    def type(self) -> Optional["StatusObject"]:
        """Объект типа сделки (статус из справочника)"""

        from utils.bitrix_utils.bitrix_objects.crm import StatusObject

        if self.type_id.value:
            return StatusObject.objects(self.but).by_status_id(status_id=self.type_id.value, entity_id="DEAL_TYPE")
        else:
            return None

    @property
    def stage(self) -> Optional["StatusObject"]:
        """Объект стадии сделки (статус из справочника)"""

        from utils.bitrix_utils.bitrix_objects.crm import StatusObject

        if self.stage_id.value:
            return StatusObject.objects(self.but).by_status_id(status_id=self.stage_id.value, entity_id=self.category.object.stage_entity_id)
        else:
            return None

    def move_to_stage(self, stage_id: Text):
        """Передвинуть сделку на конкретную стадию"""
        self.stage_id.value = stage_id
        self.save(update_fields=["stage_id"])

    def move_to_lose_stage(self):
        """Передвинуть сделку на проигранную стадию"""
        self.move_to_stage(self.category.object.lose_stage_status_id)
