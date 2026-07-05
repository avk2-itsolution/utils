from typing import Text, Type, Any, Optional, TYPE_CHECKING


if TYPE_CHECKING:
    from utils.bitrix_utils.bitrix_objects.main import BitrixObject


class BitrixField:
    """Базовый класс для Битрикс поля"""

    TYPE = "any"
    PYTHON_TYPE: Type

    def __init__(self,
                 field_code: Text,
                 *,
                 is_required: bool = False,
                 is_multiple: bool = False,
                 field_code_to_bitrix: Optional[Text] = None,
                 # не передаются вручную
                 bitrix_object: Optional["BitrixObject"] = None,
                 name: Optional[Text] = None,
                 field_attr: Optional[Text] = None,
                 # устаревшее
                 task_field_code: Optional[Text] = None):

        # Два типа инитов
        # 1) описательный инит без передачи bitrix_object
        # 2) инит для поля с передачей данных об объекте когда передан bitrix_object

        # код поля из Битрикса
        self.field_code = field_code
        # именование поле в тасках
        # 'ALLOW_CHANGE_DEADLINE', 'allowChangeDeadline'
        #  UF_AUTO_934778459549', 'ufAuto934778459549'
        self.task_field_code = task_field_code
        # код поля для отправки в Битрикс, по умолчанию совпадает с кодом из Битрикса
        self.field_code_to_bitrix = field_code_to_bitrix or self.field_code
        # если поле обязательное, то возвращаемое значение всегда будет соответствовать типу поля и не будет None
        self.is_required = is_required
        # если поле множественное, то это ВСЕГДА список из значений
        self.is_multiple = is_multiple
        self.bitrix_object = bitrix_object
        # название атрибута в bitrix_object
        self.name = name
        self.field_attr = field_attr

    def __str__(self):
        return f"{self.name} ({self.field_code})"

    def __repr__(self):
        return f"{self.name} ({self.field_code})"

    def __eq__(self, other: "BitrixField") -> bool:
        return self.field_code == other.field_code

    def __hash__(self) -> int:
        return hash(self.field_code)

    def __set_name__(self, owner: Type["BitrixObject"], name: Text):
        self.field_attr = name
        self.name = f"_{owner.__name__}__{name}"
        owner.set_bitrix_field(self)

    def __get__(self, instance: Optional["BitrixObject"], owner: Type["BitrixObject"]) -> "BitrixField":
        if instance is None:
            # если обращение из класса
            return self
        # возвращается объект с теми же даными + устанавливается bitrix_object
        return self.__class__(**(self.__dict__ | {"bitrix_object": instance}))

    def __set__(self, instance: "BitrixObject", value: Any):
        pass

    def __delete__(self, instance: "BitrixObject"):
        pass

    @property
    def raw_value(self) -> Any:
        """Значение поля без конвертации"""
        self._check_bitrix_object()
        return self.bitrix_object.get_field_value(self)

    @property
    def value(self) -> Any:
        """Получение значения"""
        self._check_bitrix_object()
        return self._get_value()

    def set_value(self, value: Any):
        # ЭТО ЖЕНИНА ВЕРСИЯ апдейта на лету!
        # Установить значение и отправить его в Битрикс24!!!
        self.bitrix_object.update_field(self.field_code, self._convert_to_bitrix(value))

    @value.setter
    def value(self, value: Any):
        """Установка значения"""
        self._check_bitrix_object()
        self._set_value(value)

    def _set_value(self, value: Any):
        """Установка значения"""

        if self.is_multiple:
            # если множественное
            if self._is_iterable(value):
                value = list(map(self._convert_to_bitrix, value))
            else:
                value = []
        else:
            value = self._convert_to_bitrix(value)

        self.bitrix_object.set_field_value(self, value)

    def _get_value(self) -> Any:
        """Получить значение из экземпляра объекта"""

        value = self.bitrix_object.get_field_value(self)

        if self.is_multiple:
            # если множественное
            if self._is_iterable(value):
                return list(map(self._convert_from_bitrix, value))
            else:
                return []
        else:
            return self._convert_from_bitrix(value)

    def _convert_from_bitrix(self, value: Any) -> Any:
        return value

    def _convert_to_bitrix(self, value: Any) -> Any:
        return value

    @property
    def bitrix_name(self) -> Text:
        """Название поля в Битриксе"""
        self._check_bitrix_object()
        return self.bitrix_object.get_field_name(self.field_code)

    @property
    def bitrix_type(self) -> Text:
        """Тип поля в Битриксе"""
        self._check_bitrix_object()
        return self.bitrix_object.get_field_type(self.field_code)

    def _check_bitrix_object(self):
        """Проверка наличия bitrix_object"""
        if not self.bitrix_object:
            raise ValueError("Вызывается из объекта класса с данными")

    def _check_single(self):
        """Проверка на одиночное поле"""
        if self.is_multiple:
            raise ValueError("Битрикс поле не одиночное")

    def _check_multiple(self):
        """Проверка на множетвенное поле"""
        if not self.is_multiple:
            raise ValueError("Битрикс поле не множественное")

    @staticmethod
    def _is_iterable(value: Any) -> bool:
        """Итерируемое ли значение"""
        try:
            iter(value)
            return True
        except TypeError:
            return False

    @property
    def eq_field_code_to_bitrix(self) -> Text:
        return f"={self.field_code_to_bitrix}"

    @property
    def ne_field_code_to_bitrix(self) -> Text:
        return f"!{self.field_code_to_bitrix}"

    @property
    def gt_field_code_to_bitrix(self) -> Text:
        return f">{self.field_code_to_bitrix}"

    @property
    def gte_field_code_to_bitrix(self) -> Text:
        return f">={self.field_code_to_bitrix}"

    @property
    def lt_field_code_to_bitrix(self) -> Text:
        return f"<{self.field_code_to_bitrix}"

    @property
    def lte_field_code_to_bitrix(self) -> Text:
        return f"<={self.field_code_to_bitrix}"

    @property
    def substr_field_code_to_bitrix(self) -> Text:
        return f"%{self.field_code_to_bitrix}"
