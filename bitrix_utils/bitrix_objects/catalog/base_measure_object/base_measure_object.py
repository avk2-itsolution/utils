from utils.bitrix_utils.bitrix_objects.catalog.base_measure_object.base_measure_object_manager import BaseMeasureObjectManager
from utils.bitrix_utils.bitrix_objects.catalog.catalog_object import CatalogObject
from utils.bitrix_utils.bitrix_objects.main.fields import (
    TextBitrixField,
    IntBitrixField,
    BoolBitrixField,
)

from typing import Dict, Text


class BaseMeasureObject(CatalogObject):
    """Единица измерения каталога (``MEASURE``) с базовыми полями Bitrix24.

    Examples:
        >>> measure = BaseMeasureObject.objects(but).get(bitrix_id=17)
        >>> measure.symbol.value
        >>> measure.url()
    """

    ENTITY_TYPE_NAME = "MEASURE"

    _objects = BaseMeasureObjectManager

    measure_title = TextBitrixField("measureTitle", is_required=True)
    code = IntBitrixField("code", is_required=True)
    is_default = BoolBitrixField("isDefault", is_required=True)
    symbol = TextBitrixField("symbol")
    symbol_intl = TextBitrixField("symbolIntl")
    symbolLetterIntl = TextBitrixField("symbolLetterIntl")

    def __str__(self):
        return self.measure_title.value

    @staticmethod
    def _validate_api_get(api_data: Dict) -> Dict:
        """Извлекает данные единицы измерения из ответа REST."""
        return api_data["measure"]

    def url(self) -> Text:
        """Возвращает URL карточки единицы измерения в портале."""
        return f"{self.portal_url}/crm/configs/measure/edit/{self.bitrix_id}/"
