from utils.bitrix_utils.bitrix_objects.catalog.catalog_object.catalog_object_manager import CatalogObjectManager

from typing import Type, TYPE_CHECKING, Dict, List

if TYPE_CHECKING:
    from utils.bitrix_utils.bitrix_objects.catalog import BaseCatalogObject


class BaseCatalogObjectManager(CatalogObjectManager):
    """Менеджер инфоблока каталога с валидацией ответов REST ``catalog.catalog``.

    Examples:
        >>> catalogs = BaseCatalogObject.objects(but).all()
        >>> for catalog in catalogs:
        ...     print(catalog.name.value)
    """

    BITRIX_OBJECT_CLASS: Type["BaseCatalogObject"]

    @staticmethod
    def _validate_api_fields(api_data: Dict) -> Dict:
        """Преобразует ответ ``getFields`` в структуру каталога."""
        return api_data["catalog"]

    @staticmethod
    def _validate_api_list(api_data: Dict) -> List:
        """Преобразует список каталогов из ответа REST."""
        return api_data["catalogs"]
