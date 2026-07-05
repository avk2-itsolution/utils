from utils.bitrix_utils.bitrix_objects.crm.crm_object.crm_object_manager import CRMObjectManager
from utils.bitrix_utils.bitrix_objects.main.exceptions import NotFoundObject, MultipleObjectsReturned

from typing import Type, Text, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from utils.bitrix_utils.bitrix_objects.crm import StatusObject


class StatusObjectManager(CRMObjectManager):
    """Менеджер элементов справочников CRM.

    Examples:
        >>> statuses = StatusObject.objects(but).by_entity_id("STATUS")
    """

    BITRIX_OBJECT_CLASS: Type["StatusObject"]

    def by_entity_id(self, entity_id: Text) -> List["BITRIX_OBJECT_CLASS"]:
        """Получить элементы справочника по типу"""
        filter_dict = {"ENTITY_ID": entity_id}
        return self.filter(filter_dict=filter_dict)

    def by_status_id(self, status_id: Text, entity_id: Optional[Text] = None) -> "BITRIX_OBJECT_CLASS":
        """Получить элемент справочника по полю STATUS_ID.
        Так как STATUS_ID не гарантирует уникальность, то можно указать тип справочника (ENTITY_ID)"""

        filter_dict = {"STATUS_ID": status_id, "ENTITY_ID": entity_id}
        status_objects = self.filter(filter_dict=filter_dict)

        if len(status_objects) == 0:
            raise NotFoundObject("Не найден элемент справочника")

        if len(status_objects) > 1:
            raise MultipleObjectsReturned("Найдено более одного элемента справочника")

        return status_objects[0]
