from utils.bitrix_utils.bitrix_objects.main.bitrix_object_manager import BitrixObjectManager
from utils.bitrix_utils.bitrix_objects.main.bitrix_object_list import BitrixObjectList

from typing import Type, Dict, Optional, Iterable, List, TYPE_CHECKING, Text

if TYPE_CHECKING:
    from utils.bitrix_utils.bitrix_objects.users import BaseUserObject


class BaseUserObjectManager(BitrixObjectManager):
    """Менеджер пользователей портала.

    Обязательные параметры REST ``user.*`` подставляются менеджером:
    - для get/list: фильтры по ID/ACTIVE и т.д.
    - для add/update: fields словарь.

    Examples:
        >>> users = BaseUserObject.objects(but).filter({"ACTIVE": True})
    """

    BITRIX_OBJECT_CLASS: Type["BaseUserObject"]

    def get_fields(self) -> Dict:
        result = self.but.call_list_method("user.fields")
        return self._validate_api_fields(result)

    def add(self, fields: Dict) -> int:
        """

        :param fields: поля из https://apidocs.bitrix24.ru/api-reference/user/user-add.html
        fields: EMAIL  обязательное поле
        :return: id пользователя
        """
        result = self.but.call_api_method("user.add", fields)["result"]
        return self._validate_api_add(result)

    def all(self,
            admin_mode: bool = False,
            order_dict: Optional[Dict] = None,
            select_only: Optional[List[Text]] = None,
            select_related: Optional[List[Text]] = None,
            timeout: Optional[int] = None) -> BitrixObjectList["BaseUserObject"]:
        """Все пользователи"""
        filter_dict = {}
        return self.filter(
            filter_dict=filter_dict,
            admin_mode=admin_mode,
            order_dict=order_dict,
            select_only=select_only,
            select_related=select_related,
            timeout=timeout)

    def filter(self,
               filter_dict: Dict,
               admin_mode: bool = False,
               order_dict: Optional[Dict] = None,
               select_only: Optional[List[Text]] = None,
               select_related: Optional[List[Text]] = None,
               timeout: Optional[int] = None) -> BitrixObjectList["BaseUserObject"]:
        """Пользователи по фильтру"""
        fields = {"ADMIN_MODE": int(admin_mode), "FILTER": filter_dict}

        if order_dict:
            fields.update({"order": order_dict})

        users = self.but.call_list_method("user.get", fields, timeout=timeout)
        users = self._validate_api_list(users)

        user_objects = BitrixObjectList(self.BITRIX_OBJECT_CLASS(user["ID"], but=self.but, bitrix_data=user) for user in users)

        if select_related:
            self.set_select_related(user_objects, select_only=select_only, select_related=select_related)

        return user_objects

    def from_ids(self,
                 user_ids: Iterable[int],
                 admin_mode: bool = False,
                 order_dict: Optional[Dict] = None,
                 select_only: Optional[List[Text]] = None,
                 select_related: Optional[List[Text]] = None,
                 timeout: Optional[int] = None) -> BitrixObjectList["BaseUserObject"]:
        """Пользователи по ID"""
        if user_ids:
            filter_dict = {"ID": list(user_ids)}
            return self.filter(
                filter_dict=filter_dict,
                admin_mode=admin_mode,
                order_dict=order_dict,
                select_only=select_only,
                select_related=select_related,
                timeout=timeout)
        else:
            return BitrixObjectList()

    def active(self, admin_mode: bool = False) -> List["BaseUserObject"]:
        """Активные пользователи"""
        return self.filter({"ACTIVE": int(True)}, admin_mode=admin_mode)

    def dismissed(self, admin_mode: bool = False) -> List["BaseUserObject"]:
        """Уволенные пользователи"""
        return self.filter({"ACTIVE": int(False)}, admin_mode=admin_mode)

    def by_xing(self, xings: Iterable[Text], admin_mode: bool = False) -> List["BaseUserObject"]:
        """Поиск по полю UF_XING"""
        return self.filter({"UF_XING": xings}, admin_mode=admin_mode)

    def current(self) -> "BaseUserObject":
        """Текущий пользователь"""
        user = self.but.call_api_method("user.current")["result"]
        return self.BITRIX_OBJECT_CLASS(user["ID"], but=self.but, bitrix_data=user)

    def search(self,
               filter_dict: Optional[Dict] = None,
               query: Optional[Text] = None,
               admin_mode: bool = False,
               order_dict: Optional[Dict] = None,
               select_only: Optional[List[Text]] = None,
               select_related: Optional[List[Text]] = None,
               timeout: Optional[int] = None) -> BitrixObjectList["BaseUserObject"]:
        """Метод для получения списка пользователей с ускоренным поиском по персональным данным (имя, фамилия, отчество, название подразделения, должность).
        Работает в двух режимах: быстро с помощью Fulltext Index и более медленный вариант через правый LIKE (поддержка определяется автоматически)"""

        fields = {"ADMIN_MODE": int(admin_mode)}

        if query:
            fields.update({"FILTER": {"FIND": query}})
        else:
            fields.update({"FILTER": filter_dict})

        if order_dict:
            fields.update({"order": order_dict})

        users = self.but.call_list_method("user.search", fields, timeout=timeout)
        users = self._validate_api_list(users)

        user_objects = BitrixObjectList(self.BITRIX_OBJECT_CLASS(user["ID"], but=self.but, bitrix_data=user) for user in users)

        if select_related:
            self.set_select_related(user_objects, select_only=select_only, select_related=select_related)

        return user_objects

    @staticmethod
    def _validate_api_fields(api_data: Dict[Text, Text]) -> Dict[Text, Dict]:
        return {field_code: {"NAME": field_name} for field_code, field_name in api_data.items()}
