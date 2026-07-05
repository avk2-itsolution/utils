from utils.bitrix_utils.bitrix_objects.crm.crm_object.crm_object_manager import CRMObjectManager

from typing import Type, Dict, Text, TYPE_CHECKING, List

if TYPE_CHECKING:
    from utils.bitrix_utils.bitrix_objects.crm.crm_item_object import CRMItemObject


class CRMItemObjectManager(CRMObjectManager):
    """Менеджер смарт-процессов.

    Обязательные параметры ``crm.item.*``:
    - entityTypeId: ID смарт-процесса (должен быть указан в наследнике CRMItemObject).
    - для add/update: fields словарь.
    """

    BITRIX_OBJECT_CLASS: Type["CRMItemObject"]

    @property
    def entity_type(self) -> Text:
        """Тип CRM-сущности"""
        return "item"

    @staticmethod
    def _validate_api_fields(api_data: Dict) -> Dict:
        return api_data["fields"]

    @staticmethod
    def _validate_api_list(api_data: Dict) -> List:
        return api_data['items']

    @staticmethod
    def _validate_api_add(api_data: Dict) -> int:
        return api_data["item"]["id"]
