from utils.bitrix_utils.bitrix_objects.crm.crm_object.crm_object_manager import CRMObjectManager

from typing import Type, TYPE_CHECKING

if TYPE_CHECKING:
    from utils.bitrix_utils.bitrix_objects.crm import BaseActivityObject


class BaseActivityObjectManager(CRMObjectManager):
    """Менеджер дел CRM.

    Обязательные параметры ``crm.activity.*`` подставляются в менеджере:
    - get/list: ownerTypeId/ownerId в полях фильтра.
    - add: поля дела (см. ``create_activity`` в CRMObject).

    Examples:
        >>> activities = BaseActivityObject.objects(but).filter({"RESPONSIBLE_ID": but.user_id})
    """

    BITRIX_OBJECT_CLASS: Type["BaseActivityObject"]
