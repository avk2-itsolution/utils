from django.utils.functional import classproperty

from utils.bitrix_utils.bitrix_objects.main import BitrixObject
from utils.bitrix_utils.bitrix_objects.catalog.catalog_object.catalog_object_manager import CatalogObjectManager

from typing import Dict, Text


class CatalogObject(BitrixObject):
    """Базовый объект каталога Bitrix24 с CRUD через REST ``catalog.*``.

    Examples:
        Создание прикладного класса каталога:
            class CustomCatalog(CatalogObject):
                ENTITY_TYPE_NAME = "CATALOG"
    """

    ID_FIELD_CODE: Text = "id"
    ENTITY_TYPE_NAME: Text = NotImplementedError

    _objects = CatalogObjectManager

    def _get_bitrix_data(self) -> Dict:
        result = self.but.call_api_method(self._get_method, {"id": self.bitrix_id})["result"]
        return self._validate_api_get(result)

    def update(self, fields: Dict):
        """Обновляет поля сущности через ``catalog.{entity_type}.update``.

        Args:
            fields (Dict): Набор полей Bitrix24 для обновления объекта.
        """
        self.but.call_api_method(self._update_method, {"id": self.bitrix_id, "fields": fields})

    def delete(self):
        """Удаляет сущность через ``catalog.{entity_type}.delete``."""
        self.but.call_api_method(self._delete_method, {"id": self.bitrix_id})

    @classproperty
    def entity_type(cls) -> Text:
        """Код сущности для REST (product, section, catalog, measure)."""
        return cls.ENTITY_TYPE_NAME.lower()

    @classproperty
    def _get_method(cls) -> Text:
        return f"catalog.{cls.entity_type}.get"

    @classproperty
    def _update_method(cls) -> Text:
        return f"catalog.{cls.entity_type}.update"

    @classproperty
    def _delete_method(cls) -> Text:
        return f"catalog.{cls.entity_type}.delete"
