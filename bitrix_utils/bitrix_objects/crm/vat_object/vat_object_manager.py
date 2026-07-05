from utils.bitrix_utils.bitrix_objects.crm.crm_object.crm_object_manager import CRMObjectManager

from typing import Type, TYPE_CHECKING

if TYPE_CHECKING:
    from utils.bitrix_utils.bitrix_objects.crm import VATObject


class VATObjectManager(CRMObjectManager):
    """Менеджер ставок НДС CRM.

    Examples:
        >>> VATObject.objects(but).all()
    """

    BITRIX_OBJECT_CLASS: Type["VATObject"]
