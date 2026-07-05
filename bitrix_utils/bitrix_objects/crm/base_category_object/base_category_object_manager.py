from utils.bitrix_utils.bitrix_objects.crm.crm_object.crm_object_manager import CRMObjectManager

from typing import Type, TYPE_CHECKING, Dict, List

if TYPE_CHECKING:
    from utils.bitrix_utils.bitrix_objects.crm import BaseCategoryObject


class BaseCategoryObjectManager(CRMObjectManager):
    """Менеджер воронок CRM.

    Examples:
        >>> categories = DealCategory.objects(but).all()
    """

    BITRIX_OBJECT_CLASS: Type["BaseCategoryObject"]

    @staticmethod
    def _validate_api_add(api_data: Dict) -> int:
        return api_data["category"]["id"]

    @staticmethod
    def _validate_api_list(api_data: Dict) -> List:
        return api_data["categories"]

    @staticmethod
    def _validate_api_fields(api_data: Dict) -> List:
        return api_data["fields"]
