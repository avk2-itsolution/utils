from django.core.serializers.json import DjangoJSONEncoder
from django.utils.functional import classproperty

from utils.bitrix_utils.bitrix_objects.main.bitrix_object_manager import BitrixObjectManager
from utils.bitrix_utils.bitrix_objects.main.fields.bitrix_field import BitrixField

import importlib
import json
from typing import Optional, Dict, Type, Any, Text, Union, ForwardRef, List, Iterable

BitrixUserToken = ForwardRef("BitrixUserToken")


class BitrixObject:
    """Базовый объект Bitrix: хранит данные, поля и ссылки на менеджер.

    Examples:
        >>> obj = TaskObject(123, but=but)  # любой наследник BitrixObject
        >>> obj.save(update_fields=["title"])
    """

    """
    если TaskObject(BaseTaskObject(BitrixObject)):

    from bitrix_objects_local.tasks.task_object.task_object import TaskObject
    from bitrix_objects_local.tokens import get_admin_token
    title = TaskObject(11333, but=get_admin_token()).title.value

    # Получить поля задач
    q= TaskObject.objects(evg_but).get_fields()

    # Используем фильтр
    TaskObject.title.field_code_to_bitrix
    вернет "TITLE
    поэтому фильтруем
    qq =TaskObject.objects(evg_but).filter({TaskObject.title.field_code_to_bitrix: 'Создание Чат-бота на основе Многоцелевого бота'})


    """

    # код поля-идентификатора
    ID_FIELD_CODE: Text = "ID"

    # нужно ли кэшировать (1-й раз создался объект с каким-то ID, 2-й раз берется из кэша)
    CACHEABLE: bool = False
    # словарь вида: {bitrix_id: bitrix_object}
    CACHE: Optional[Dict[int, "BitrixObject"]] = None

    CONVERT_RULE_NONE = 0
    # Когда в АПИ Y или N как булеаны, а записывать как Y N
    CONVERT_RULE_YN = 1
    # Когда может вернуть строку с интом внутри
    CONVERT_RULE_INT = 2
    CONVERT_RULE_DATE = 3
    # Когда в АПИ Y или N как булеаны, а устанавлиивать надо 1 и 0
    CONVERT_RULE_YN_SET_1_0 = 4
    # Когда универсальные списки, например, отдают 01.05.2024 16:33:11
    CONVERT_RULE_DATE_DOTTED = 5

    # поля из Битрикса
    _fields: Optional[Dict[Text, Any]] = None
    # объявленные поля в коде (заполняются автоматически): {field_code: BitrixField}
    _bitrix_fields: Optional[Dict[Text, BitrixField]] = None
    # Менеджер объектов
    _objects = BitrixObjectManager

    @classproperty
    def objects(cls) -> Type["BitrixObjectManager"]:
        """Менеджер Битрикс-объектов"""
        cls._objects.BITRIX_OBJECT_CLASS = cls
        return cls._objects

    def __new__(cls, bitrix_id: int, **kwargs: Any):
        if cls.CACHEABLE:
            # берем объект из кеша
            if cls.CACHE is None:
                # чтобы CACHE был именно из того класса, объект которого создается, а не из базового
                cls.CACHE = {}
            return cls.CACHE.setdefault(bitrix_id, super().__new__(cls))
        else:
            return super().__new__(cls)

    def __init__(self, bitrix_id: Union[int, Text], *, but: BitrixUserToken, bitrix_data: Optional[Dict] = None):
        self.bitrix_id = int(bitrix_id)
        # TODO можно придумать токен по умолчанию
        # self.but = but or get_token.get_super_token()
        self.but = but
        # После or идет для того досстать __bitrix_data из кеша.... смотреть __new___
        # __new__ встроенный класс метод который вызвается перед __init__
        self.__bitrix_data = bitrix_data or getattr(self, f"_{self.__class__.__name__}__bitrix_data", None)
        self.__update_fields: Dict[BitrixField: Any] = {}

    def __bool__(self):
        return bool(self.bitrix_id)

    def __repr__(self):
        # return f"{type(self).__name__}(id={self.id})"
        return f"{self.__class__.__name__} {self.bitrix_id}"

    def __str__(self):
        # Попытка сделать атоматическую функцию для читаемого представления
        # print(user) -> id=1 Хлобыстин Евгений
        segments = [s for s in [
            f"id={self.bitrix_id}",
            self.bitrix_data.get('LAST_NAME'),
            self.bitrix_data.get('NAME'),
            self.bitrix_data.get('TITLE'),
        ] if s
                    ]
        # Ромин вариант
        # return f"{self.__class__.__name__} {self.bitrix_id}"

        return " ".join(segments)

    def __eq__(self, other: "BitrixObject") -> bool:
        return self.bitrix_id == other.bitrix_id

    def __hash__(self) -> int:
        return hash(self.bitrix_id)

    def __getitem__(self, key: Text) -> Any:
        """Берет значение Битрикс-поля по его коду,
        в приориете те значения, которые сохранены локально"""
        return (self.bitrix_data | self.local_data).get(key)

    @property
    def bitrix_data(self) -> Dict[Text, Any]:
        """Данные из Битрикса"""
        if self.__bitrix_data is None:
            self.__bitrix_data = self._get_bitrix_data()
        return self.__bitrix_data

    @property
    def local_data(self) -> Dict[Text, Any]:
        """Локально сохраненные данные"""
        return {bitrix_field.field_code: value for bitrix_field, value in self.__update_fields.items()}

    @property
    def fields_to_bitrix(self) -> Dict[Text, Any]:
        """Поля для обновления в Битрикс"""
        return {bitrix_field.field_code_to_bitrix: value for bitrix_field, value in self.__update_fields.items()}

    @property
    def named_bitrix_data(self) -> Dict:
        """Значения полей из Битрикс с названиями вместо кодов"""
        named_bitrix_data = {}
        for field_code, value in self.bitrix_data.items():
            key = self.get_field_name(field_code)
            named_bitrix_data[key] = value
        return named_bitrix_data

    @property
    def fields(self) -> Dict[Text, Dict]:
        """Поля Битрикс-сущности"""
        if self._fields is None:
            self.__class__._fields = self.objects(self.but).get_fields()
        return self._fields

    @classproperty
    def bitrix_fields(cls) -> Dict[Text, BitrixField]:
        return cls._bitrix_fields

    def __clear_cached_fields(self):
        """Почистить закэшированные поля"""
        if self.bitrix_fields:
            for bitrix_field in self.bitrix_fields.values():
                if hasattr(self, bitrix_field.name):
                    # если поле закэшировано, удаляем его
                    delattr(self, bitrix_field.name)

    def refresh_from_api(self):
        """Подтянуть актуальные данные из Битрикса"""
        self.__bitrix_data = self._get_bitrix_data()
        self.__update_fields.clear()
        self.__clear_cached_fields()

    def __update_bitrix_data(self, update_fields: Optional[Iterable[Text]] = None):
        """Обновить данные из Битрикса локальными.
        В update_fields передаются атрибуты, значения которых нужно обновить.
        Если update_fields не указан, то обновляются все, которые есть в локально сохраненных"""

        # выбранные Битрикс поля
        bitrix_fields: List[BitrixField] = []

        if self.__bitrix_data is not None:
            local_data = self.local_data

            if update_fields is not None:
                # если указаны конкретные атрибуты

                field_codes: List[Text] = []

                # по указанным атрибутам ищутся коды полей, которые приходят из Битрикса
                for field_attr in update_fields:
                    bitrix_field: BitrixField = getattr(self, field_attr)
                    bitrix_fields.append(bitrix_field)
                    field_codes.append(bitrix_field.field_code)

                # фильтрация локально сохраненных данных (берем только те, чей код поля из Битрикса был найден выше)
                local_data = {field_code: value for field_code, value in local_data.items() if field_code in field_codes}

            self.__bitrix_data.update(local_data)

        if bitrix_fields:
            # если указаны конкретные Битрикс поля, обновляем только их
            for bitrix_field in bitrix_fields:
                del self.__update_fields[bitrix_field]
        else:
            # иначе очищаем все
            self.__update_fields.clear()

    def save(self, update_fields: Optional[Iterable[Text]] = None):
        """Сохранить в Битриксе локально сохраненные значения"""

        fields_to_bitrix = self.fields_to_bitrix

        if update_fields is not None:
            # если указаны конкретные атрибуты

            field_codes_to_bitrix: List[Text] = []

            for field_attr in update_fields:
                bitrix_field: BitrixField = getattr(self, field_attr)
                field_codes_to_bitrix.append(bitrix_field.field_code_to_bitrix)

            fields_to_bitrix = {field_code_to_bitrix: value for field_code_to_bitrix, value in fields_to_bitrix.items() if field_code_to_bitrix in field_codes_to_bitrix}

        if fields_to_bitrix:
            self.update(fields_to_bitrix)
            self.__update_bitrix_data(update_fields)

    def _get_bitrix_data(self) -> Dict:
        raise NotImplementedError

    def update(self, fields: Dict):
        """Обновить в Битриксе"""
        raise NotImplementedError

    def delete(self):
        """Удалить из Битрикса"""
        raise NotImplementedError

    @staticmethod
    def _validate_api_get(api_data: Any) -> Any:
        return api_data

    def get_field_value(self, bitrix_field: BitrixField) -> Any:
        """Получить значение поля, смотреть __getitem__"""
        return self[bitrix_field.field_code]

    def set_field_value(self, bitrix_field: BitrixField, value: Any):
        """Установить значение"""
        self.__update_fields.update({bitrix_field: value})

    def get_field_data(self, field_code: Text) -> Dict:
        """Словарь данных о поле"""
        return self.fields.get(field_code, {})

    def get_field_items(self, field_code: Text) -> Dict[int, Any]:
        """Варианты значения поля для списка"""
        field = self.get_field_data(field_code)
        items = field.get("items", [])
        return {int(item["ID"]): item["VALUE"] for item in items}

    def get_field_values(self, field_code: Text) -> Dict[Text, Any]:
        """Варианты значения поля для перечисления"""
        field = self.get_field_data(field_code)
        values = field.get("items", {})
        return {value['ID']: value['VALUE'] for value in values}

    def get_field_name(self, field_code: Text) -> Text:
        """Название поля в Битриксе"""
        field = self.get_field_data(field_code)
        return field.get("formLabel") or field.get("title") or field.get("NAME") or field.get("name") or field_code

    def get_field_type(self, field_code: Text) -> Optional[Text]:
        """Тип поля в Битриксе"""
        field = self.get_field_data(field_code)
        return field.get("type") or field.get("TYPE")

    @property
    def portal_domain(self) -> Text:
        """Домен портала"""
        if getattr(self.but.user, "portal", None):
            # если BitrixUserToken из bitrix_utils
            return self.but.user.portal.domain
        else:
            # если BitrixUserToken из integration_utils
            from django.conf import settings
            return settings.APP_SETTINGS.portal_domain

    @property
    def portal_url(self) -> Text:
        """Ссылк на портал"""
        return f"https://{self.portal_domain}"

    @property
    def url(self) -> Text:
        """Ссылка на объект"""
        raise NotImplementedError

    @property
    def html_link(self) -> Text:
        """HTML-ссылка на объект"""
        return f"<a href={self.url}>{self}<a>"

    @property
    def is_cloud_portal(self) -> bool:
        """Портал является облачным?"""
        return self.portal_domain.endswith(".bitrix24.ru")

    @property
    def is_box_portal(self) -> bool:
        """Портал является коробочным?"""
        return not self.is_cloud_portal

    @classmethod
    def get_class(cls, bitrix_class: Union[Type["BitrixObject"], Text]) -> Type["BitrixObject"]:
        """Получение класса в виде объекта"""
        if isinstance(bitrix_class, str):
            return cls.import_class(bitrix_class)
        elif isinstance(type(bitrix_class), type):
            return bitrix_class
        else:
            raise TypeError("Параметр не является ни Битрик-классом, ни путем к нему")

    @staticmethod
    def import_class(class_path: Text) -> Type["BitrixObject"]:
        """Получение класса в виде объекта по его пути"""
        module_path, class_name = class_path.rsplit(".", maxsplit=1)
        module = importlib.import_module(module_path)
        return getattr(module, class_name)

    def html_tag(self, text=None):
        if not text:
            text = str(self)
        return f'<a href="{self.url}">{text}</a>'

    def set_bitrix_data(self, bitrix_data: Optional[Dict]):
        """Установка bitrix_data"""
        self.__bitrix_data = bitrix_data

    @classmethod
    def set_fields(cls, fields: Optional[Dict]):
        """Установка fields"""
        cls._fields = fields

    @classmethod
    def set_bitrix_field(cls, bitrix_field: BitrixField):
        """Установка fields"""
        if cls._bitrix_fields is None:
            cls._bitrix_fields = {bitrix_field.field_code: bitrix_field}
        else:
            cls._bitrix_fields = cls._bitrix_fields | {bitrix_field.field_code: bitrix_field}

    def to_dict(self,
                select_only: Optional[List[Text]] = None,
                select_related: Optional[List[Text]] = None,
                prefetch_related: bool = True) -> Dict[Text, Any]:
        """Получение словаря на основе объекта.
        Если указан select_only, то берутся только те поля, которые в списке, иначе все.
        Если указан select_related, то подтягиваются еще и связанные объекты"""

        from utils.bitrix_utils.bitrix_objects.main.fields import ObjectBitrixField

        if prefetch_related:
            self.objects(self.but).set_select_related([self], select_only=select_only, select_related=select_related)

        # получаем поля, которые нужно выбрать
        select_only_dict: Dict[Text, List[Text]] = self.objects.parse_select(select_only or [])
        # получаем поля, удаленные объкты в которых нужно подтянуть
        select_related_dict: Dict[Text, List[Text]] = self.objects.parse_select(select_related or [])

        result_dict: Dict[Text, Any] = {"bitrix_id": self.bitrix_id}

        # для каждого объялвенного Битрикс-поля в классе Битрикс-объекта
        for bitrix_field_from_cls in self.bitrix_fields.values():
            # получение Битрикс-поля из Битрикс-объекта
            bitrix_field: BitrixField = getattr(self, bitrix_field_from_cls.field_attr)

            if not (select_only is None or bitrix_field.field_attr in select_only_dict):
                # если указан select_only и в нем не указано поле, то пропускаем его
                continue

            if bitrix_field.field_attr in select_related_dict:
                # если атрибут передан в select_related
                if not isinstance(bitrix_field, ObjectBitrixField):
                    raise TypeError(f"Атрибут {bitrix_field.field_attr} не является объектом ObjectBitrixField")

                new_select_only: Optional[List[Text]] = select_only_dict.get(bitrix_field.field_attr)
                new_select_related: Optional[List[Text]] = select_related_dict.get(bitrix_field.field_attr)

                if bitrix_field.value:
                    # если есть значение, рекурсивно подтягиваем данные из связанных объектов

                    if bitrix_field.is_multiple:
                        # если поле множественное
                        result_dict[bitrix_field.field_attr] = [bitrix_object.to_dict(select_only=new_select_only, select_related=new_select_related, prefetch_related=False) for bitrix_object in bitrix_field.objects]
                    else:
                        # если поле единичное
                        result_dict[bitrix_field.field_attr] = bitrix_field.object.to_dict(select_only=new_select_only, select_related=new_select_related, prefetch_related=False)
                else:
                    result_dict[bitrix_field.field_attr] = bitrix_field.value
            else:
                if bitrix_field.value and (hasattr(bitrix_field, "to_dict") or hasattr(bitrix_field, "to_dicts")):
                    if bitrix_field.is_multiple:
                        # если поле множественное
                        result_dict[bitrix_field.field_attr] = bitrix_field.to_dicts()
                    else:
                        # если поле единичное
                        result_dict[bitrix_field.field_attr] = bitrix_field.to_dict()
                else:
                    result_dict[bitrix_field.field_attr] = bitrix_field.value

        return result_dict

    def to_json(self,
                select_only: Optional[List[Text]] = None,
                select_related: Optional[List[Text]] = None,
                prefetch_related: bool = True) -> Text:
        """ Получение json строки с полями из объекта """
        return json.dumps(self.to_dict(select_only=select_only, select_related=select_related, prefetch_related=prefetch_related), ensure_ascii=False, cls=DjangoJSONEncoder)

    def unify_field(self, field, value):
        # Перенести за пределы класса потом
        # Унификация для работы в Python Коде

        from integration_utils.iu_datetime.dt_its import dt_its

        if field[2] in [BitrixObject.CONVERT_RULE_YN, BitrixObject.CONVERT_RULE_YN_SET_1_0]:
            return True if value in ['Y', True, 1, '1'] else False
        if field[2] == BitrixObject.CONVERT_RULE_INT:
            if not value:
                return 0
            return int(value)
        if field[2] == BitrixObject.CONVERT_RULE_DATE:
            return dt_its(value) if value else None
        if field[2] == BitrixObject.CONVERT_RULE_DATE_DOTTED:
            from dateutil.parser import parse
            return dt_its(parse(value, dayfirst=True)) if value else None
        return value

    def de_unify_field(self, field, value):
        # Из нормальных переменных делает переменные для API
        if field[2] == BitrixObject.CONVERT_RULE_YN:
            if value in ['Y', True, 1, '1']:
                return 'Y'  # ТУТ ЕЩЕ БЫВАЕТ Y
            elif value in ['N', False, None, 0, '0']:
                return 'N'  # ТУТ ЕЩЕ БЫВАЕТ N
            else:
                raise ValueError('')
        if field[2] == BitrixObject.CONVERT_RULE_YN_SET_1_0:
            if value in ['Y', True, 1, '1']:
                return '1'  # ТУТ ЕЩЕ БЫВАЕТ Y
            elif value in ['N', False, None, 0, '0']:
                return '0'  # ТУТ ЕЩЕ БЫВАЕТ N
            else:
                raise ValueError('')

        return value

    def get_field(self, field):
        # Получает поле задачи и приводит к типу адекватному
        value = self.bitrix_data.get(field[1])
        return self.unify_field(field, value)

    def update_field(self, field, value):
        # Это нужно переопределить, т.к. разные методы вызватся tasks.task.update или crm.deal.update
        # В слушчае с tasks результат апдейта возвращает поля задачи новые..., но с пользоватльскими есть нюанс, можно использовать логику для оптимизации количества запросов
        raise NotImplemented
        """
        Пример:
        task = self.but.call_api_method('tasks.task.update', {
            'taskId': self.id,
            'fields': {field[0]: value}
        })['result']['task']
        if self._bitrix_data:
            self._bitrix_data.update(task)
        if not task.get(field[1]):
            # Значит update не возвращает пользовательское поле
            # придется обновлять из API, можно было бы установить зная.. но на всякий случай лучше перечитать будет
            # self._bitrix_data[field[1]] = value
            self._bitrix_data = None
        """

    def set_field(self, field_name, value):
        # приводим к битриксовому виду значение
        # value = self.de_unify_field(field, value)
        # Вызываем метод обновления его переопределяем для кажого класса
        self.update_field(field_name, value)
        return self.bitrix_data

    def control_field(self, field, value):
        # Контроллирует значение поля, и если надо меняет
        # field должно быть равно value, если так, то ничего не делаем
        # Если не сходится, то меняем
        if self.get_field(field) == self.unify_field(field, value):
            return self.bitrix_data
        else:
            # ilogger.info('task_object', f'Перекинут мяч в задаче {self.id}', log_to_cron=True)
            return self.set_field(field, value)
