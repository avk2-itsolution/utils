from utils.bitrix_utils.bitrix_objects.crm.crm_object.crm_object_manager import CRMObjectManager

from typing import Type, TYPE_CHECKING

if TYPE_CHECKING:
    from utils.bitrix_utils.bitrix_objects.crm import BaseContactObject


class BaseContactObjectManager(CRMObjectManager):
    """Менеджер контактов CRM.

    Обязательные параметры REST подставляются менеджером:
    - entityTypeId: ``3``.
    - для add/update: fields словарь.

    Examples:
        >>> contacts = BaseContactObject.objects(but).filter({"HAS_EMAIL": True})
    """

    BITRIX_OBJECT_CLASS: Type["BaseContactObject"]
