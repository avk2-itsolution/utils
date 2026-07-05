from utils.bitrix_utils.bitrix_objects.crm.crm_sale_object.crm_sale_object_manager import CRMSaleObjectManager
from utils.bitrix_utils.bitrix_objects.main.bitrix_object_list import BitrixObjectList

from typing import Type, TYPE_CHECKING

if TYPE_CHECKING:
    from utils.bitrix_utils.bitrix_objects.crm import BaseLeadObject, StatusObject


class BaseLeadObjectManager(CRMSaleObjectManager):
    """Менеджер лидов CRM.

    Обязательные параметры REST подставляются менеджером:
    - entityTypeId: ``1``.
    - для add/update: fields словарь.

    Examples:
        >>> leads = BaseLeadObject.objects(but).filter({"ASSIGNED_BY_ID": but.user_id})
        >>> statuses = BaseLeadObject.objects(but).get_statuses()
    """

    BITRIX_OBJECT_CLASS: Type["BaseLeadObject"]

    def get_statuses(self) -> BitrixObjectList["StatusObject"]:
        """Получить статусы (стадии) лида"""
        from utils.bitrix_utils.bitrix_objects.crm import StatusObject
        return StatusObject.objects(self.but).by_entity_id("STATUS")
