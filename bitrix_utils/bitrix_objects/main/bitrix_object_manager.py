from utils.bitrix_utils.bitrix_objects.main.bitrix_object_list import BitrixObjectList
from utils.bitrix_utils.bitrix_objects.main.exceptions import MultipleObjectsReturned

import importlib
from typing import Dict, Optional, List, Iterable, TYPE_CHECKING, Type, Any, ForwardRef, Tuple, Text, Set

if TYPE_CHECKING:
    from utils.bitrix_utils.bitrix_objects.main import BitrixObject

BitrixUserToken = ForwardRef("BitrixUserToken")


class BitrixObjectManager:
    """Базовый менеджер BitrixObject: create/filter/list с but-сессией.

    Examples:
        >>> objs = SomeObject.objects(but).filter({"ACTIVE": True})
        >>> new_obj = SomeObject.objects(but).create({"NAME": "Demo"})
    """

    BITRIX_OBJECT_CLASS: Type["BitrixObject"]

    def __init__(self, but: BitrixUserToken):
        self.but = but
        # атрибут класса присваивается арибуту объекта
        self.BITRIX_OBJECT_CLASS = self.BITRIX_OBJECT_CLASS

    object_path = NotImplemented

    def get_fields(self) -> Dict[Text, Dict]:
        raise NotImplementedError

    def add(self, fields: Dict) -> int:
        """Добавить и получить bitrix_id"""
        raise NotImplementedError

    def create(self, fields: Dict) -> "BitrixObject":
        """Добавить и получить Битрикс-объект"""
        bitrix_id = self.add(fields)
        return self.BITRIX_OBJECT_CLASS(bitrix_id, but=self.but)

    def all(self,
            order_dict: Optional[Dict] = None,
            # select_list: Optional[Iterable] = None,
            select_only: Optional[List[Text]] = None,
            select_related: Optional[List[Text]] = None,
            timeout: Optional[int] = None) -> BitrixObjectList:
        """Все элементы"""
        raise NotImplementedError

    def filter(self,
               filter_dict: Dict,
               order_dict: Optional[Dict] = None,
               # select_list: Optional[Iterable] = None,
               select_only: Optional[List[Text]] = None,
               select_related: Optional[List[Text]] = None,
               timeout: Optional[int] = None) -> BitrixObjectList:
        """Элементы по фильтру"""
        raise NotImplementedError

    def from_id(self, bitrix_id: int) -> "BitrixObject":
        return self.BITRIX_OBJECT_CLASS(bitrix_id, but=self.but)

    def from_ids(self,
                 object_ids: Iterable[int],
                 order_dict: Optional[Dict] = None,
                 # select_list: Optional[Iterable] = None,
                 select_only: Optional[List[Text]] = None,
                 select_related: Optional[List[Text]] = None,
                 timeout: Optional[int] = None) -> List["BitrixObject"]:
        """Элементы по ID"""
        raise NotImplementedError

    def get_or_create(self,
                      filter_dict: Dict,
                      default_fields: Optional[Dict] = None,
                      ignore_multiple: bool = False,
                      filter_after_api: Optional[Dict] = None) -> Tuple["BitrixObject", bool]:
        """Ищет объект на портале по полям из filter_dict,
        если не находит, то создает с полями из filter_dict и default_fields"""

        if default_fields is None:
            default_fields = {}

        bitrix_objects = self.filter(filter_dict)

        if filter_after_api is not None:
            bitrix_objects = bitrix_objects.filter(**filter_after_api)

        if bitrix_objects.length > 1:
            if ignore_multiple:
                # берем последний элемент
                return bitrix_objects.last(), False
            else:
                raise MultipleObjectsReturned("Найдено больше одного объекта")

        if bitrix_objects.length == 1:
            return bitrix_objects.first(), False

        return self.create(filter_dict | default_fields), True

    def update_or_create(self,
                         filter_dict: Dict,
                         default_fields: Optional[Dict] = None,
                         ignore_multiple: bool = False,
                         filter_after_api: Optional[Dict] = None) -> Tuple["BitrixObject", bool]:
        """Ищет объект на портале по полям из filter_dict,
        если находит, то обновляет поля из default_fields,
        если не находит, то создает с полями из filter_dict и default_fields"""

        if default_fields is None:
            default_fields = {}

        bitrix_objects = self.filter(filter_dict)

        if filter_after_api is not None:
            bitrix_objects = bitrix_objects.filter(**filter_after_api)

        if bitrix_objects.length > 1:
            if ignore_multiple:
                # берем последний элемент
                return bitrix_objects.last(), False
            else:
                raise MultipleObjectsReturned("Найдено больше одного объекта")

        if bitrix_objects.length == 1:
            bitrix_object = bitrix_objects.first()
            bitrix_object.update(default_fields)
            return bitrix_object, False

        return self.create(filter_dict | default_fields), True

    @staticmethod
    def _validate_api_add(api_data: Any) -> Any:
        return api_data

    @staticmethod
    def _validate_api_list(api_data: Any) -> Any:
        return api_data

    @staticmethod
    def _validate_api_fields(api_data: Any) -> Any:
        return api_data

    @staticmethod
    def get_ids(bitrix_objects: List["BitrixObject"]) -> List[int]:
        """Получить список ID"""
        return [bitrix_object.bitrix_id for bitrix_object in bitrix_objects]

    @staticmethod
    def get_dict(bitrix_objects: List["BitrixObject"]) -> Dict[int, "BitrixObject"]:
        """Получить словарь вида {bitrix_id: bitrix_object}"""
        return {bitrix_object.bitrix_id: bitrix_object for bitrix_object in bitrix_objects}

    def set_select_related(self,
                           bitrix_objects: List["BitrixObject"],
                           select_only: Optional[List[Text]] = None,
                           select_related: Optional[List[Text]] = None):
        """Подтягивает и устанавливает связанные объекты"""

        from utils.bitrix_utils.bitrix_objects.main.fields import ObjectBitrixField

        # получаем поля, которые нужно выбрать
        select_only_dict: Dict[Text, List[Text]] = self.parse_select(select_only or [])
        # получаем поля, удаленные объкты в которых нужно подтянуть
        select_related_dict: Dict[Text, List[Text]] = self.parse_select(select_related or [])

        # словарь, где для каждого поля будут собраны ID объектов, которые нужно подтянуть
        related_object_ids: Dict[Text, List[int]] = {}

        # собираем ID связанных объектов для
        for field_attr in select_related_dict.keys():
            # является ли поле объектом ObjectBitrixField
            self.__check_object_bitrix_field(field_attr)

            if not (select_only is None or field_attr in select_only_dict):
                # если указан select_only и в нем не указано поле, то пропускаем его
                continue

            for bitrix_object in bitrix_objects:
                bitrix_field: ObjectBitrixField = getattr(bitrix_object, field_attr)

                if bitrix_field.value:
                    # если поле не пустое
                    if bitrix_field.is_multiple:
                        # если множественное поле (bitrix_field.value - список bitrix_id)
                        related_object_ids.setdefault(field_attr, []).extend(bitrix_field.value)
                    else:
                        # если единичное поле (bitrix_field.value - bitrix_id)
                        related_object_ids.setdefault(field_attr, []).append(bitrix_field.value)

        for field_attr, object_ids in related_object_ids.items():
            # получаем объект Битрикс поле по названию атрибута
            bitrix_field: ObjectBitrixField = getattr(self.BITRIX_OBJECT_CLASS, field_attr)

            new_select_only: Optional[List[Text]] = select_only_dict.get(bitrix_field.field_attr)
            new_select_related: Optional[List[Text]] = select_related_dict.get(bitrix_field.field_attr)

            # получаем объект класса
            object_class = self.BITRIX_OBJECT_CLASS.get_class(bitrix_field.object_type)
            # рекурсивно подтягиваем связанные объекты
            related_objects: List["BitrixObject"] = object_class.objects(self.but).from_ids(object_ids, select_only=new_select_only, select_related=new_select_related)
            # получаем словарь вида: {bitrix_id: bitrix_object}
            related_objects_dict: Dict[int, "BitrixObject"] = self.get_dict(related_objects)

            for bitrix_object in bitrix_objects:
                bitrix_field = getattr(bitrix_object, field_attr)

                if bitrix_field.value:
                    # если поле не пустое
                    if bitrix_field.is_multiple:
                        # если множественное поле
                        related_objects = [related_objects_dict[bitrix_id] for bitrix_id in bitrix_field.value]
                        bitrix_field.set_cached_value(related_objects)
                    else:
                        # если единичное поле
                        related_object = related_objects_dict[bitrix_field.value]
                        bitrix_field.set_cached_value(related_object)

    @staticmethod
    def parse_select(select: List[Text]) -> Dict[Text, List[Text]]:
        """Из списка вида: ["field", "field1__field11", "field1__field12__field121"]
         формирует словарь вида: {field: [], field1: ["field11", "field12__field121"]}"""

        select_dict: Dict[Text, List[Text]] = {}

        for string in select:
            field_attr, *new_select = string.split("__", maxsplit=1)
            select_dict.setdefault(field_attr, []).extend(new_select)

        return select_dict

    def __check_object_bitrix_field(self, field_attr: Text):
        """Проверка на то, является ли атрибут объектом ObjectBitrixField"""

        from utils.bitrix_utils.bitrix_objects.main.fields import ObjectBitrixField

        bitrix_field = getattr(self.BITRIX_OBJECT_CLASS, field_attr, None)
        if not isinstance(bitrix_field, ObjectBitrixField):
            raise TypeError(f"Атрибут {field_attr} не является объектом ObjectBitrixField")

    def mix_select_list_and_select_only(self, select_list: Optional[Iterable[Text]], select_only: Optional[List[Text]]) -> Optional[List[Text]]:
        """Смешивает поля, котрые переданы в select_list and select_only"""

        from utils.bitrix_utils.bitrix_objects.main.fields import BitrixField

        if select_list is None is select_only:
            return None

        select_set: Set[Text] = set(select_list or [])
        select_set.add(self.BITRIX_OBJECT_CLASS.ID_FIELD_CODE)

        select_only_dict: Dict[Text, List[Text]] = self.parse_select(select_only or [])

        for field_attr in select_only_dict.keys():
            bitrix_field: Optional[BitrixField] = getattr(self.BITRIX_OBJECT_CLASS, field_attr, None)
            if bitrix_field:
                select_set.add(bitrix_field.field_code_to_bitrix)

        return list(select_set)

    def get_all(self):
        # groups = self.but.call_list_method('sonet_group.get', {'IS_ADMIN': 'Y'})
        # return ResponseList(groups)
        raise NotImplemented

    def api_list(self):
        raise NotImplemented

    def get_object_class(self) -> Type:
        # TODO порядок проперти и констурктора класса! проврить
        # для избежания кросс импортов пришлось написать эту функцию, а в наследниках BitrixObjectManager указывать путь к соотвессвующему объекту
        # например object_path = 'main_placement.classes.deal_object.DealObject'
        path, name = self.object_path.rsplit('.', maxsplit=1)
        module = importlib.import_module(path)
        return getattr(module, name)

    def from_ids_list(self, ids_list: List[int]) -> List['BitrixObject']:
        return [self.get_object_class()(x, but=self.but) for x in ids_list]

    def to_ids_list(self, result_list: List[object]) -> List[int]:
        # Превратить список объектов в список id
        return [int(x['ID']) for x in result_list]
