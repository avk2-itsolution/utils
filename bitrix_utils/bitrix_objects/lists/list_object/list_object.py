from utils.bitrix_utils.bitrix_objects.lists.list_object.list_object_manager import ListObjectManager
from utils.bitrix_utils.bitrix_objects.main import BitrixObject
from utils.bitrix_utils.bitrix_objects.main.fields import (
    BitrixField,
    IntBitrixField,
    TextBitrixField,
    BoolBitrixField,
    FileBitrixField,
)

from typing import Dict, Text, Any, Union, List, Optional


class ListObject(BitrixObject):
    """Элемент списка (УС/ИБ) с IBLOCK_ID/TYPE (нужно указать в наследнике).

    Examples:
        class DealList(ListObject):
            IBLOCK_ID = 10

        >>> elem = DealList.objects(but).get(bitrix_id=5)
        >>> elem.fields_to_bitrix
        >>> elem.url
    """

    IBLOCK_TYPE_ID: Text = "lists"
    IBLOCK_ID = NotImplementedError

    SOCNET_GROUP_ID = None

    _objects = ListObjectManager

    name = TextBitrixField("NAME", is_required=True)
    iblock_id = IntBitrixField("IBLOCK_ID", is_required=True)
    iblock_code = TextBitrixField("IBLOCK_CODE")
    iblock_section_id = IntBitrixField("IBLOCK_SECTION_ID")
    created_by = IntBitrixField("CREATED_BY", is_required=True)
    bp_published = BoolBitrixField("BP_PUBLISHED", is_required=True)
    code = TextBitrixField("CODE")

    def __str__(self):
        return self.name.value

    def _get_bitrix_data(self) -> Dict:
        result = self.but.call_api_method("lists.element.get", {"IBLOCK_TYPE_ID": self.IBLOCK_TYPE_ID, "IBLOCK_ID": self.IBLOCK_ID, "SOCNET_GROUP_ID": self.SOCNET_GROUP_ID, "ELEMENT_ID": self.bitrix_id})["result"][0]
        return self._validate_api_get(result)

    def update(self, fields: Dict):
        """Обновить элемент"""
        self.but.call_api_method("lists.element.update", {"IBLOCK_TYPE_ID": self.IBLOCK_TYPE_ID, "IBLOCK_ID": self.IBLOCK_ID, "SOCNET_GROUP_ID": self.SOCNET_GROUP_ID, "ELEMENT_ID": self.bitrix_id, "FIELDS": fields})

    def delete(self):
        """Удалить элемент"""
        self.but.call_api_method("lists.element.delete", {"IBLOCK_TYPE_ID": self.IBLOCK_TYPE_ID, "IBLOCK_ID": self.IBLOCK_ID, "SOCNET_GROUP_ID": self.SOCNET_GROUP_ID, "ELEMENT_ID": self.bitrix_id})

    @property
    def fields_to_bitrix(self) -> Dict[Text, Any]:
        """Поля для обновления в Битрикс.
        Для элемента УС нужно указывать значения всех полей при обновлении, кроме файловых полей.
        При указании значений файловых полей, которые приходят из Битрикс, может быть ошибка, поэтому их убираем"""
        return {field_code: value for field_code, value in self.bitrix_data.items() if not self._is_file_field(field_code)} | super().fields_to_bitrix

    def _is_file_field(self, field_code: Text) -> bool:
        """Файловое ли поле"""
        bitrix_field = self.bitrix_fields.get(field_code)
        return isinstance(bitrix_field, FileBitrixField)

    def get_field_value(self, bitrix_field: BitrixField) -> Any:
        value = super().get_field_value(bitrix_field)

        if isinstance(bitrix_field, FileBitrixField) and not isinstance(value, list):
            # если файловое поле и данные из bitrix_data
            raise TypeError("Невозможно получить значение файлового поля из элемента УС")

        if isinstance(value, dict):
            # если пользовательское поле
            if bitrix_field.is_multiple:
                return list(value.values())
            else:
                return next(iter(value.values()))

        return value

    def get_file_url(self, bitrix_field: IntBitrixField) -> Union[Optional[Text], List[Text]]:
        """Получить ссылку на скачивание файла. Для скачивания требуется авторизация"""

        value = bitrix_field.value

        if value:
            file_urls = self.but.call_list_method("lists.element.get.file.url", {
                "IBLOCK_TYPE_ID": self.IBLOCK_TYPE_ID,
                "IBLOCK_ID": self.IBLOCK_ID,
                "SOCNET_GROUP_ID": self.SOCNET_GROUP_ID,
                "ELEMENT_ID": self.bitrix_id,
                "FIELD_ID": bitrix_field.field_code.replace("PROPERTY_", "")
            })
        else:
            file_urls = []

        if bitrix_field.is_multiple:
            return file_urls
        else:
            return next(iter(file_urls)) if file_urls else None

    @property
    def url(self) -> Text:
        """Ссылка на элемент списка"""

        if self.is_cloud_portal:
            path = "company"
        else:
            path = "services"

        return f"{self.portal_url}/{path}/lists/{self.IBLOCK_ID}/element/0/{self.bitrix_id}/"
