from utils.bitrix_utils.bitrix_objects.main.bitrix_object_manager import BitrixObjectManager
from utils.bitrix_utils.bitrix_objects.main.bitrix_object_list import BitrixObjectList
from utils.bitrix_utils.bitrix_objects.groups.constants import SELECT_FIELDS

from typing import Dict, Iterable, Optional, List, Type, TYPE_CHECKING, Text

if TYPE_CHECKING:
    from utils.bitrix_utils.bitrix_objects.groups import BaseGroupObject


class BaseGroupObjectManager(BitrixObjectManager):
    """Базовый менеджер объектов групп.

    Examples:
        >>> groups = BaseGroupObject.objects(but).all()
        >>> projects = BaseGroupObject.objects(but).filter({"PROJECT": True})
    """

    BITRIX_OBJECT_CLASS: Type["BaseGroupObject"]

    def add(self, fields: Dict) -> int:
        """Добавить группу"""
        result = self.but.call_api_method("sonet_group.create", fields)["result"]
        return self._validate_api_add(result)

    def all(self,
            order_dict: Optional[Dict] = None,
            select_list: Optional[Iterable] = SELECT_FIELDS,
            select_only: Optional[List[Text]] = None,
            select_related: Optional[List[Text]] = None,
            timeout: Optional[int] = None) -> BitrixObjectList["BaseGroupObject"]:
        """Все группы"""
        filter_dict = {}
        return self.filter(filter_dict=filter_dict,
                           order_dict=order_dict,
                           select_list=select_list,
                           select_only=select_only,
                           select_related=select_related,
                           timeout=timeout)

    def filter(self,
               filter_dict: Dict,
               order_dict: Optional[Dict] = None,
               select_list: Iterable = SELECT_FIELDS,
               select_only: Optional[List[Text]] = None,
               select_related: Optional[List[Text]] = None,
               timeout: Optional[int] = None) -> BitrixObjectList["BaseGroupObject"]:
        """Группы по фильтру"""

        select_list = self.mix_select_list_and_select_only(select_list, select_only)

        fields = {"filter": filter_dict, "select": select_list}

        if order_dict:
            fields.update({"order": order_dict})

        groups = self.but.call_list_method("socialnetwork.api.workgroup.list", fields, timeout=timeout)
        groups = self._validate_api_list(groups)

        group_objects = BitrixObjectList(self.BITRIX_OBJECT_CLASS(group["ID"], but=self.but, bitrix_data=group) for group in groups)

        if select_related:
            self.set_select_related(group_objects, select_only=select_only, select_related=select_related)

        return group_objects

    def from_ids(self,
                 group_ids: Iterable[int],
                 order_dict: Optional[Dict] = None,
                 select_list: Optional[Iterable] = SELECT_FIELDS,
                 select_only: Optional[List[Text]] = None,
                 select_related: Optional[List[Text]] = None,
                 timeout: Optional[int] = None) -> BitrixObjectList["BaseGroupObject"]:
        """Группы по ID"""
        if group_ids:
            filter_dict = {"ID": list(group_ids)}
            return self.filter(
                filter_dict=filter_dict,
                order_dict=order_dict,
                select_list=select_list,
                select_only=select_only,
                select_related=select_related,
                timeout=timeout)
        else:
            return BitrixObjectList()

    @staticmethod
    def _validate_api_list(api_data: Dict) -> List:
        """В списочном методе поля приходят в camelCase и притом не все"""

        def from_camel_to_upper(field_code: Text) -> Text:
            result = []
            for char in field_code:
                if char.isupper():
                    result.append('_')
                result.append(char.upper())
            return ''.join(result)

        field_map: Dict[Text, Text] = {}
        return list(map(lambda bitrix_data: {field_map.setdefault(key, from_camel_to_upper(key)): value for key, value in bitrix_data.items()}, api_data["workgroups"]))

    def user_groups(self) -> Dict["BaseGroupObject", Dict[Text, Text]]:
        """Получить список групп текущего пользователя.
        Возвращает словарь вида: {user_object: {"GROUP_NAME": название группы, "ROLE": роль}}"""

        groups = self.but.call_list_method("sonet_group.user.groups")
        return {self.BITRIX_OBJECT_CLASS(group["GROUP_ID"], but=self.but): {"GROUP_NAME": group["GROUP_NAME"], "ROLE": group["ROLE"]} for group in groups}
