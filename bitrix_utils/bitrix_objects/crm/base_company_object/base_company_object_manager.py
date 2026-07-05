from utils.bitrix_utils.bitrix_objects.crm.crm_object.crm_object_manager import CRMObjectManager

from typing import Type, TYPE_CHECKING

if TYPE_CHECKING:
    from utils.bitrix_utils.bitrix_objects.crm import BaseCompanyObject


class BaseCompanyObjectManager(CRMObjectManager):
    """Менеджер компаний CRM.

    Обязательные параметры REST подставляются менеджером:
    - entityTypeId: ``4``.
    - для add/update: fields словарь.

    Examples:
        >>> companies = BaseCompanyObject.objects(but).filter({"HAS_PHONE": True})
    """

    BITRIX_OBJECT_CLASS: Type["BaseCompanyObject"]
