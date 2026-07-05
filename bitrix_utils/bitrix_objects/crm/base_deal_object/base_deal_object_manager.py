from utils.bitrix_utils.bitrix_objects.crm.crm_sale_object.crm_sale_object_manager import CRMSaleObjectManager

from typing import Type, TYPE_CHECKING

if TYPE_CHECKING:
    from utils.bitrix_utils.bitrix_objects.crm import BaseDealObject


class BaseDealObjectManager(CRMSaleObjectManager):
    """Менеджер сделок CRM.

    Обязательные параметры REST подставляются менеджером:
    - entityTypeId: ``2``.
    - для add/update: fields словарь.

    Examples:
        >>> deals = BaseDealObject.objects(but).filter({"CATEGORY_ID": 1})
    """

    BITRIX_OBJECT_CLASS: Type["BaseDealObject"]
