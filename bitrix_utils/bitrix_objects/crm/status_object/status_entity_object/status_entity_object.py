from utils.bitrix_utils.bitrix_objects.crm.crm_object import CRMObject
from utils.bitrix_utils.bitrix_objects.crm.status_object.status_entity_object.status_entity_object_manager import StatusEntityObjectManager
from utils.bitrix_utils.bitrix_objects.main.exceptions import NotFoundObject
from utils.bitrix_utils.bitrix_objects.main.fields import (
    TextBitrixField,
    IntBitrixField,
    BoolBitrixField,
    DictBitrixField,
)

from typing import Text, ForwardRef, Dict, Optional, List

BitrixUserToken = ForwardRef("BitrixUserToken")


class StatusEntityObject(CRMObject):
    """Класс объекта типа справочника"""

    STATUS_OBJECT = "utils.bitrix_utils.bitrix_objects.crm.StatusObject"

    _objects = StatusEntityObjectManager

    name = TextBitrixField("NAME", is_required=True)
    semantic_info = DictBitrixField("SEMANTIC_INFO")
    prefix = TextBitrixField("PREFIX")
    field_attribute_scope = TextBitrixField("FIELD_ATTRIBUTE_SCOPE")
    entity_type_id = IntBitrixField("ENTITY_TYPE_ID")
    is_enabled = BoolBitrixField("IS_ENABLED")
    category_id = IntBitrixField("CATEGORY_ID")

    def __init__(self, bitrix_id: Text, *, but: BitrixUserToken, bitrix_data: Optional[Dict] = None):
        super().__init__(0, but=but, bitrix_data=bitrix_data)
        self.bitrix_id = str(bitrix_id)

    def __str__(self):
        return self.name.value

    def _get_bitrix_data(self) -> Dict:
        for status_type_object in self.objects(but=self.but).all():
            if status_type_object.bitrix_id == self.bitrix_id:
                return status_type_object.bitrix_data
        raise NotFoundObject("Не найден тип справочника")

    @property
    def statuses(self) -> List["STATUS_OBJECT"]:
        """Элементы типа справочника"""
        status_object = self.import_class(self.STATUS_OBJECT)
        return status_object.objects(but=self.but).by_entity_id(entity_id=self.bitrix_id)

    @property
    def url(self) -> Text:
        """Ссылка на Справочники"""
        return f"{self.portal_url}/crm/configs/status/"
