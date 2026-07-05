from utils.bitrix_utils.bitrix_objects.crm.crm_object.crm_object_manager import CRMObjectManager

from typing import Type, TYPE_CHECKING

if TYPE_CHECKING:
    from utils.bitrix_utils.bitrix_objects.crm.crm_sale_object import CRMSaleObject


class CRMSaleObjectManager(CRMObjectManager):
    """Менеджер объектов сущностей продажи (лид или сделка)"""

    BITRIX_OBJECT_CLASS: Type["CRMSaleObject"]
