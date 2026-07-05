from utils.bitrix_utils.bitrix_objects.main.fields import BitrixField
from utils.bitrix_utils.bitrix_objects.main.bitrix_object_list import BitrixObjectList
from utils.bitrix_utils.bitrix_objects.utils.files import FileObject
from utils.bitrix_utils.bitrix_objects.utils.multifield import MultifieldObject

from typing import Text, Type, Any, Optional, Union, Dict, List, TYPE_CHECKING
from datetime import date, time, datetime
from dateutil.parser import parse

if TYPE_CHECKING:
    from utils.bitrix_utils.bitrix_objects.main import BitrixObject
    from utils.bitrix_utils.bitrix_objects.crm.crm_object import CRMObject


class CachedBitrixField(BitrixField):
    """Базовый класс для полей, значение которых кэшируется в self.name"""

    @property
    def value(self) -> Any:
        if self.has_cached_value():
            # если есть в кэше, берем из него
            return self._convert_cached_value(self.get_cached_value())
        else:
            return super().value

    @value.setter
    def value(self, value: Any):
        """Установка значения"""
        self._check_bitrix_object()
        # установка нового значения
        self._set_value(value)
        # удаление старого значения из кэша
        self.del_cached_value()

    def has_cached_value(self) -> bool:
        """Есть ли закэшированное значение"""
        return bool(self.get_cached_value())

    def get_cached_value(self) -> Any:
        """Получить закэшированное значение"""
        return getattr(self.bitrix_object, self.name, None)

    def set_cached_value(self, value: Any):
        """Установить закэшированное значение"""
        setattr(self.bitrix_object, self.name, value)

    def del_cached_value(self):
        """Удалить закэшированное значение"""
        self.set_cached_value(None)

    def _convert_cached_value(self, value: Any) -> Any:
        """Конвертация закэшированного значения в тот тип, который приходит из Битрикса"""
        return value


class TextBitrixField(BitrixField):
    """Текстовое поле"""

    TYPE = "string"
    PYTHON_TYPE = str

    def _convert_from_bitrix(self, value: Any) -> Optional[Text]:
        if self.is_required or value:
            return str(value)
        else:
            return None

    _convert_to_bitrix = _convert_from_bitrix


class LinkBitrixField(TextBitrixField):
    """Текстовое поле в виде ссылки"""

    def get_html_tag(self, text: Optional[Text] = None) -> Text:
        self._check_bitrix_object()
        return f"<a href='{self.value}'>{text or self.bitrix_name}</a>"


class IntBitrixField(BitrixField):
    """Целочисленное поле"""

    TYPE = "integer"
    PYTHON_TYPE = int

    def _convert_from_bitrix(self, value: Optional[Union[Text, int]]) -> Optional[int]:
        if self.is_required or value:
            return int(value)
        else:
            return None

    _convert_to_bitrix = _convert_from_bitrix


class FloatBitrixField(BitrixField):
    """Поле вещественногго числа"""

    TYPE = "decimal"
    PYTHON_TYPE = float

    def _convert_from_bitrix(self, value: Optional[Union[Text, int, float]]) -> Optional[float]:
        if self.is_required or value:
            return float(value)
        else:
            return

    _convert_to_bitrix = _convert_from_bitrix


class BoolBitrixField(BitrixField):
    """Булево поле"""

    TYPE = "boolean"
    PYTHON_TYPE = bool
    VARIABLES = {0: False, 1: True, '0': False, '1': True, 'N': False, 'Y': True, True: True, False: False}

    def _convert_from_bitrix(self, value: Optional[Union[Text, int]]) -> Optional[bool]:
        if self.is_required or value is not None:
            return self.VARIABLES[value]
        else:
            return None

    def _convert_to_bitrix(self, value: Optional[bool]) -> Optional[bool]:
        if self.is_required or value is not None:
            return bool(value)
        else:
            return None


class BoolCharBitrixField(BoolBitrixField):
    VARIABLES = {'N': False, 'Y': True, 'D': None}
    CONVERTED_VARIABLES = {value: key for key, value in VARIABLES.items()}

    def _convert_from_bitrix(self, value: Text) -> Optional[bool]:
        return self.VARIABLES[value]

    def _convert_to_bitrix(self, value: Optional[bool]) -> Text:
        return self.CONVERTED_VARIABLES[value]


class DateBitrixField(BitrixField):
    """Поле даты"""

    TYPE = "date"
    PYTHON_TYPE = date

    def _convert_from_bitrix(self, value: Optional[Text]) -> Optional[date]:
        if self.is_required or value:
            # берем первые 10 символов из ISO-формата: YYYY-mm-dd
            try:
                return date.fromisoformat(value[:10])
            except ValueError:
                return parse(value[:10], dayfirst=True).date()
        else:
            return None

    def _convert_to_bitrix(self, value: Optional[date]) -> Optional[Text]:
        if self.is_required or value:
            return value.isoformat()
        else:
            return None


class TimeBitrixField(BitrixField):
    """Поле времени"""

    TYPE = "time"
    PYTHON_TYPE = time

    def _convert_from_bitrix(self, value: Optional[Text]) -> Optional[time]:
        if self.is_required or value:
            return time.fromisoformat(value)
        else:
            return None

    def _convert_to_bitrix(self, value: Optional[time]) -> Optional[Text]:
        if self.is_required or value:
            return value.isoformat()
        else:
            return None


class DateTimeBitrixField(BitrixField):
    """Поле даты и времени"""

    TYPE = "datetime"
    PYTHON_TYPE = datetime

    def _convert_from_bitrix(self, value: Optional[Text]) -> Optional[datetime]:
        if self.is_required or value:
            try:
                return datetime.fromisoformat(value)
            except ValueError:
                return parse(value, dayfirst=True)
        else:
            return None

    def _convert_to_bitrix(self, value: Optional[datetime]) -> Optional[Text]:
        if self.is_required or value:
            return value.isoformat()
        else:
            return None


class ListBitrixField(BitrixField):
    """Списочное поле"""

    TYPE = "array"
    PYTHON_TYPE = int

    def __init__(self, field_code: Text, *, _items: Optional[Dict] = None, **kwargs):
        super().__init__(field_code, **kwargs)
        self._items = _items

    @property
    def items(self) -> Dict[int, Any]:
        """Варианты значений поля, словарь вида: {ID значения: значение}"""
        self._check_bitrix_object()
        if self._items is None:
            self._items = self.bitrix_object.get_field_items(self.field_code)
        return self._items

    @property
    def display_value(self) -> Any:
        """Пользовательское значение"""

        value = self.value

        if self.is_multiple:
            return list(map(self.items.get, value))
        else:
            return self.items.get(value)

    def to_dict(self) -> Optional[Dict]:
        self._check_single()

        if self.value:
            return {"id": self.value, "value": self.display_value}
        else:
            return self.value

    def to_dicts(self) -> List[Dict]:
        self._check_multiple()
        return [{"id": value, "value": value} for value_id, value in zip(self.value, self.display_value)]

    def _convert_from_bitrix(self, value: Optional[Union[int, Text]]) -> Optional[int]:
        if self.is_required or value:
            return int(value)
        else:
            return None

    def _convert_to_bitrix(self, value: Optional[Union[int, Text]]) -> Optional[int]:
        if self.is_required or value:
            return int(value)
        else:
            return None


class EnumBitrixField(BitrixField):
    """Перечисление"""

    TYPE = "enum"
    PYTHON_TYPE = str

    def __init__(self, field_code: Text, *, _values: Optional[Dict] = None, **kwargs):
        super().__init__(field_code, **kwargs)
        self._values = _values

    @property
    def values(self) -> Dict[Text, Any]:
        """Варианты значений поля, словарь вида: {Индентификатор значения: значение}"""
        self._check_bitrix_object()
        if not self._values:
            self._values = self.bitrix_object.get_field_values(self.field_code)
        return self._values

    @property
    def display_value(self) -> Any:
        """Пользовательское значение"""

        value = self.value

        if self.is_multiple:
            return list(map(self.values.get, value))
        else:
            return self.values.get(value)

    def to_dict(self) -> Optional[Dict]:
        self._check_single()

        if self.value:
            return {"id": self.value, "value": self.display_value}
        else:
            return self.value

    def to_dicts(self) -> List[Dict]:
        self._check_multiple()
        return [{"id": value, "value": value} for value_id, value in zip(self.value, self.display_value)]

    def _convert_from_bitrix(self, value: Optional[Union[int, Text]]) -> Optional[Text]:
        if self.is_required or value:
            return str(value)
        else:
            return None

    def _convert_to_bitrix(self, value: Optional[Union[int, Text]]) -> Optional[Text]:
        if self.is_required or value:
            return str(value)
        else:
            return None


class FileBitrixField(CachedBitrixField):
    """Поле файла"""

    TYPE = "file"
    PYTHON_TYPE = FileObject

    def __init__(self, field_code: Text, *, is_crm_entity: bool = False, **kwargs: Any):
        super().__init__(field_code, **kwargs)
        # is_crm_entity = True, когда поле в стандартном элементе CRM (не в смарт-проценссах)
        self.is_crm_entity = is_crm_entity

    @CachedBitrixField.value.setter
    def value(self, value: Optional[FileObject]):
        """Установка значения"""
        self._check_bitrix_object()
        # установка нового значения
        self._set_value(value)
        # удаление старого значения из кэша
        self.del_cached_value()
        # сохранение нового значения в кэш
        self.set_cached_value(value)

    def to_dict(self) -> Optional[Dict]:
        self._check_single()

        if self.value:
            return self.value.to_dict()
        else:
            return self.value

    def to_dicts(self) -> List[Dict]:
        self._check_multiple()
        return [file_object.to_dict() for file_object in self.value]

    def _convert_from_bitrix(self, value: Optional[Union[Dict, List]]) -> Optional[FileObject]:
        if self.is_required or value:
            if isinstance(value, dict) and value.get("id"):
                # если из Битрикса
                if value.get("downloadUrl"):
                    url = f"https://{self.bitrix_object.portal_domain}{value['downloadUrl']}"
                else:
                    url = value["urlMachine"]

                return FileObject.from_url(url)

            else:
                # если из local_data
                if isinstance(value, dict):
                    value = value["fileData"]

                return FileObject.from_list(value)
        else:
            return None

    def _convert_to_bitrix(self, value: Optional[FileObject]) -> Optional[Union[List, Dict]]:
        if self.is_required or value:
            if self.is_crm_entity:
                return {"fileData": value.to_list}
            else:
                return value.to_list
        else:
            return None


class DictBitrixField(BitrixField):
    """JSON поле"""

    TYPE = "json"
    PYTHON_TYPE = dict

    def _convert_from_bitrix(self, value: Optional[Dict]) -> Optional[Dict]:
        if self.is_required or value:
            return dict(value)
        else:
            return None

    def _convert_to_bitrix(self, value: Optional[Dict]) -> Optional[Dict]:
        if self.is_required or value:
            return dict(value)
        else:
            return None


class ObjectBitrixField(CachedBitrixField):
    """Поле Битрикс объекта"""

    TYPE = "object"

    def __init__(self,
                 field_code: Text,
                 *,
                 object_type: Union[Type["BitrixObject"], Text],
                 bitrix_id_field_type: Type[BitrixField] = IntBitrixField,
                 **kwargs: Any):

        super().__init__(field_code, **kwargs)
        # класс Битрикс-объекта
        self.object_type = object_type
        # тип поля индентификатора Битрикс объекта
        self.bitrix_id_field_type = bitrix_id_field_type

    @property
    def object_class(self) -> Type["BitrixObject"]:
        """Получение класса в виде объекта по его пути"""
        if isinstance(self.object_type, str):
            return self.bitrix_object.import_class(self.object_type)
        else:
            return self.object_type

    @property
    def object(self) -> Optional["BitrixObject"]:
        """Связанный объект"""

        self._check_single()

        if self.has_cached_value():
            # берем из кеша, если есть
            return self.get_cached_value()

        if self.value is not None:
            bitrix_object = self.object_class(self.value, but=self.bitrix_object.but)
            self.set_cached_value(bitrix_object)
            return bitrix_object
        else:
            return None

    @object.setter
    def object(self, value: Optional["BitrixObject"]):
        self._check_single()
        self.value = getattr(value, "bitrix_id", None)
        self.set_cached_value(value)

    @property
    def objects(self) -> BitrixObjectList["BitrixObject"]:
        """Связанные объекты"""
        self._check_multiple()

        if self.has_cached_value():
            # берем из кеша, если есть
            return BitrixObjectList(self.get_cached_value())

        bitrix_objects = BitrixObjectList(self.object_class(bitrix_id, but=self.bitrix_object.but) for bitrix_id in self.value)
        self.set_cached_value(bitrix_objects)
        return bitrix_objects

    @objects.setter
    def objects(self, value: List["BitrixObject"]):
        from utils.bitrix_utils.bitrix_objects.main import BitrixObject
        self._check_multiple()
        self.value = BitrixObject.objects.get_ids(value)
        self.set_cached_value(value)

    def _convert_from_bitrix(self, value: Optional[int]) -> Optional[Union[int, Text]]:
        if self.is_required or value:
            return self.bitrix_id_field_type.PYTHON_TYPE(value)
        else:
            return None

    def _convert_to_bitrix(self, value: Optional[Union[int, Text]]) -> Optional[Union[int, Text]]:
        if self.is_required or value:
            return self.bitrix_id_field_type.PYTHON_TYPE(value)
        else:
            return None

    def _convert_cached_value(self, value: "BitrixObject") -> Union[Optional[Union[int, Text]], List[Union[int, Text]]]:
        if self.is_multiple:
            return [bitrix_object.bitrix_id for bitrix_object in value]
        else:
            return value.bitrix_id


class UfCrmObjectBitrixField(ObjectBitrixField):
    """
    Поле для CRM сущностей в пользовательских полях в смарт-процессах.
    В смарт-процессах может приходить не просто ID сущности (числом), но и ID с префиксом вида 'D_112182', 'CO_112206' и т.п.
    """

    object_type: Type["CRMObject"]

    def _convert_from_bitrix(self, value: Optional[Text]) -> Optional[int]:
        if isinstance(value, str):
            value = int(value.split('_', maxsplit=1)[-1])
        return super()._convert_from_bitrix(value)

    def _convert_to_bitrix(self, value: Optional[int]) -> Optional[Text]:
        if value:
            return f"{self.object_type.ENTITY_TYPE_ABBR}_{super()._convert_to_bitrix(value)}"
        else:
            return super()._convert_to_bitrix(value)


class MultiBitrixField(BitrixField):
    """Множественное поле. Применяется для хранения телефонов, email-адресов и другой контактной информации"""

    TYPE = "multifield"
    PYTHON_TYPE = MultifieldObject

    def __init__(self, field_code: Text, **kwargs: Any):
        kwargs.update({"is_required": True, "is_multiple": True})
        super().__init__(field_code, **kwargs)

    def to_dicts(self) -> List[Dict]:
        return [multifield_object.to_dict() for multifield_object in self.value]

    def _convert_from_bitrix(self, value: Dict[Text, Text]) -> MultifieldObject:
        return MultifieldObject.from_dict(value)

    def _convert_to_bitrix(self, value: MultifieldObject) -> Dict[Text, Text]:
        return value.to_dict()


class UfCrmObjectField(ObjectBitrixField):
    """
    Поле для CRM сущностей в пользовательских полях в смарт-процессах.
    В смарт-процессах может приходить не просто ID сущности (числом), но и ID с префиксом вида 'D_112182', 'CO_112206' и т.п.
    """

    def __init__(self, field_code: Text, prefix: Optional[Text] = None, **kwargs: Any):
        super().__init__(field_code, **kwargs)

        # префикс для записи ID сущности
        # "D" - deal
        # "L" - lead
        # "C" - contact
        # "CO" - company
        # Смарты - T(id в 16-ричной системе), например T42c_1654

        self._prefix = prefix

    def _convert_from_bitrix(self, value: Text) -> int:
        value = int(value.split('_')[-1])
        return super()._convert_from_bitrix(value)

    def _convert_to_bitrix(self, value: Any) -> Any:
        if self._prefix:
            return f'{self._prefix}_{value}'
        return value
