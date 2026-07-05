from utils.bitrix_utils.bitrix_objects.crm.crm_object.crm_object_manager import CRMObjectManager

from typing import Type, List, TYPE_CHECKING

if TYPE_CHECKING:
    from utils.bitrix_utils.bitrix_objects.crm import StatusEntityObject


class StatusEntityObjectManager(CRMObjectManager):
    """Менеджер объектов типов справочника"""

    BITRIX_OBJECT_CLASS: Type["StatusEntityObject"]

    def all(self, *args, **kwargs) -> List["StatusEntityObject"]:
        """Все элементы"""
        status_entities = self.but.call_list_method("crm.status.entity.types")
        return [self.BITRIX_OBJECT_CLASS(bitrix_id=status_entity[self.BITRIX_OBJECT_CLASS.ID_FIELD_CODE], but=self.but, bitrix_data=status_entity) for status_entity in status_entities]
