from utils.bitrix_utils.bitrix_objects.crm.base_category_object.base_category_object_manager import BaseCategoryObjectManager
from utils.bitrix_utils.bitrix_objects.crm.crm_object import CRMObject
from utils.bitrix_utils.bitrix_objects.main.bitrix_object_list import BitrixObjectList
from utils.bitrix_utils.bitrix_objects.main.fields import (
    TextBitrixField,
    IntBitrixField,
    BoolBitrixField,
)

from typing import Dict, Text, TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from utils.bitrix_utils.bitrix_objects.crm import StatusObject


class BaseCategoryObject(CRMObject):
    """Категория/воронка CRM (наследуется под конкретную сущность).

    Examples:
        class DealCategory(BaseCategoryObject):
            ENTITY_TYPE_ID = 2
            CRM_OBJECT = "utils.bitrix_utils.bitrix_objects.crm.BaseDealObject"
    """

    ENTITY_TYPE_NAME = "CATEGORY"
    USER_FIELD_ENTITY_ID = "CRM_CATEGORY"

    ID_FIELD_CODE = "id"

    CRM_OBJECT: Text = NotImplementedError

    _objects = BaseCategoryObjectManager

    name = TextBitrixField("name", is_required=True)
    entity_type_id = IntBitrixField("entityTypeId", is_required=True)
    sort = IntBitrixField("sort", is_required=True)
    is_default = BoolBitrixField("isDefault", is_required=True)
    origin_id = IntBitrixField("originId")
    originator_id = IntBitrixField("originatorId")
    is_system = BoolBitrixField("isSystem")
    code = TextBitrixField("code")

    def __str__(self):
        return self.name.value

    def __bool__(self):
        # ID может равняться 0
        return self.bitrix_id is not None

    @property
    def stage_entity_id(self) -> Text:
        """ID типа справочника со стадиями для текущей воронки"""

        crm_class = self.get_class(self.CRM_OBJECT)

        if self.bitrix_id:
            return f"{crm_class.ENTITY_TYPE_NAME}_STAGE_{self.bitrix_id}"
        else:
            return f"{crm_class.ENTITY_TYPE_NAME}_STAGE"

    @property
    def stages(self) -> BitrixObjectList["StatusObject"]:
        """Стадии текущей воронки (статусы из справочника)"""
        from utils.bitrix_utils.bitrix_objects.crm import StatusObject
        return StatusObject.objects(self.but).by_entity_id(self.stage_entity_id)

    @property
    def stage_status_prefix(self) -> Text:
        """Префикс кода стадии для текущей воронки"""

        if self.bitrix_id:

            crm_class = self.get_class(self.CRM_OBJECT)

            if crm_class.is_smart_process:
                # если смарт-процесс
                return f"D{crm_class.ENTITY_TYPE_ABBR}_{self.bitrix_id}:"

            else:
                return f"C{self.bitrix_id}:"

        else:
            return ""

    @property
    def new_stage_status_id(self) -> Text:
        """Код первичной стадии для текущей воронки"""
        return f"{self.stage_status_prefix}NEW"

    @property
    def lose_stage_status_id(self) -> Text:
        """Код проигранной стадии для текущей воронки"""
        return f"{self.stage_status_prefix}LOSE"

    @property
    def new_stage(self) -> Optional["StatusObject"]:
        """Первичной стадия для текущей воронки (статус из справочника)"""
        from utils.bitrix_utils.bitrix_objects.crm import StatusObject
        return StatusObject.objects(self.but).by_status_id(status_id=self.new_stage_status_id, entity_id=self.stage_entity_id)

    @property
    def lose_stage(self) -> Optional["StatusObject"]:
        """Проигранная стадия для текущей воронки (статус из справочника)"""
        from utils.bitrix_utils.bitrix_objects.crm import StatusObject
        return StatusObject.objects(self.but).by_status_id(status_id=self.lose_stage_status_id, entity_id=self.stage_entity_id)

    @staticmethod
    def _validate_api_get(api_data: Dict) -> Dict:
        return api_data["category"]
