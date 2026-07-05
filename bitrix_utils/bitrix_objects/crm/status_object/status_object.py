from utils.bitrix_utils.bitrix_objects.crm.crm_object import CRMObject
from utils.bitrix_utils.bitrix_objects.crm.status_object.status_object_manager import StatusObjectManager
from utils.bitrix_utils.bitrix_objects.main.fields import (
    TextBitrixField,
    IntBitrixField,
    BoolBitrixField,
    DictBitrixField,
    ObjectBitrixField,
)

from typing import Text


class StatusObject(CRMObject):
    """Элемент справочника CRM (стадии, типы и т.п.).

    Examples:
        >>> status = StatusObject.objects(but).by_status_id(status_id="NEW", entity_id="STATUS")
        >>> status.name.value
    """

    ENTITY_TYPE_NAME = "STATUS"
    USER_FIELD_ENTITY_ID = "CRM_STATUS"

    STATUS_ENTITY_OBJECT = "utils.bitrix_utils.bitrix_objects.crm.StatusEntityObject"

    _objects = StatusObjectManager

    entity = ObjectBitrixField("ENTITY_ID", object_type=STATUS_ENTITY_OBJECT, bitrix_id_field_type=TextBitrixField, is_required=True)
    status_id = TextBitrixField("STATUS_ID", is_required=True)
    name = TextBitrixField("NAME", is_required=True)
    name_init = TextBitrixField("NAME_INIT")
    sort = IntBitrixField("SORT")
    system = BoolBitrixField("SYSTEM")
    category_id = IntBitrixField("CATEGORY_ID")
    color = TextBitrixField("COLOR")
    semantics = TextBitrixField("SEMANTICS")
    extra = DictBitrixField("EXTRA")

    def __str__(self):
        return self.name.value

    @property
    def url(self) -> Text:
        """Ссылка на Справочники"""
        return f"{self.portal_url}/crm/configs/status/"
