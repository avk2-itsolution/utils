from utils.bitrix_utils.bitrix_objects.catalog.catalog_object.catalog_object_manager import CatalogObjectManager

from typing import Type, TYPE_CHECKING, Dict, List

if TYPE_CHECKING:
    from utils.bitrix_utils.bitrix_objects.catalog import BaseMeasureObject


class BaseMeasureObjectManager(CatalogObjectManager):
    """Менеджер единиц измерения с подстановкой ключей ответов ``measure``/``measures``.

    Examples:
        >>> measures = BaseMeasureObject.objects(but).all()
        >>> default = next((m for m in measures if m.is_default.value), None)
    """

    BITRIX_OBJECT_CLASS: Type["BaseMeasureObject"]

    @staticmethod
    def _validate_api_fields(api_data: Dict) -> Dict:
        """Преобразует ответ ``getFields`` в структуру единицы измерения."""
        return api_data["measure"]

    @staticmethod
    def _validate_api_add(api_data: Dict) -> Dict:
        """Возвращает идентификатор созданной единицы измерения."""
        return api_data["measure"]["id"]

    @staticmethod
    def _validate_api_list(api_data: Dict) -> List:
        """Преобразует список единиц измерения из ответа REST."""
        return api_data["measures"]
