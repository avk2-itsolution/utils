from utils.bitrix_utils.bitrix_objects.crm.crm_item_object.crm_item_object_manager import CRMItemObjectManager

from typing import Type, TYPE_CHECKING

if TYPE_CHECKING:
    from utils.bitrix_utils.bitrix_objects.crm import BaseInvoiceObject


class BaseInvoiceObjectManager(CRMItemObjectManager):
    """Менеджер объектов счетов"""

    BITRIX_OBJECT_CLASS: Type["BaseInvoiceObject"]
