from utils.bitrix_utils.bitrix_objects.main.bitrix_object_list import BitrixObjectList
from utils.bitrix_utils.bitrix_objects.main.bitrix_object_manager import BitrixObjectManager

from typing import TYPE_CHECKING, Type, Dict, Optional, List, Text, Iterable

if TYPE_CHECKING:
    from utils.bitrix_utils.bitrix_objects.departments.base_department_object import BaseDepartmentObject


class BaseDepartmentObjectManager(BitrixObjectManager):
    """Менеджер объектов подразделений портала.

    Examples:
        >>> deps = BaseDepartmentObject.objects(but).filter({"NAME": "Отдел продаж"})
        >>> all_deps = BaseDepartmentObject.objects(but).all()
    """

    BITRIX_OBJECT_CLASS: Type["BaseDepartmentObject"]

    def get_fields(self) -> Dict:
        result = self.but.call_list_method("department.fields")
        return self._validate_api_fields(result)

    def add(self, fields: Dict) -> int:
        result = self.but.call_api_method("department.add", fields)["result"]
        return self._validate_api_add(result)

    def all(self,
            order_dict: Optional[Dict] = None,
            select_only: Optional[List[Text]] = None,
            select_related: Optional[List[Text]] = None,
            timeout: Optional[int] = None) -> BitrixObjectList["BaseDepartmentObject"]:
        """Все подразделения"""

        filter_dict = {}

        return self.filter(
            filter_dict=filter_dict,
            order_dict=order_dict,
            select_only=select_only,
            select_related=select_related,
            timeout=timeout)

    def filter(self,
               filter_dict: Dict,
               order_dict: Optional[Dict] = None,
               select_only: Optional[List[Text]] = None,
               select_related: Optional[List[Text]] = None,
               timeout: Optional[int] = None) -> BitrixObjectList["BaseDepartmentObject"]:
        """Подразделения по фильтру"""

        fields = {"FILTER": filter_dict}

        if order_dict:
            fields.update({"order": order_dict})

        departments = self.but.call_list_method("department.get", fields, timeout=timeout)
        departments = self._validate_api_list(departments)

        department_objects = BitrixObjectList(self.BITRIX_OBJECT_CLASS(department["ID"], but=self.but, bitrix_data=department) for department in departments)

        if select_related:
            self.set_select_related(department_objects, select_only=select_only, select_related=select_related)

        return department_objects

    def from_ids(self,
                 department_ids: Iterable[int],
                 order_dict: Optional[Dict] = None,
                 select_only: Optional[List[Text]] = None,
                 select_related: Optional[List[Text]] = None,
                 timeout: Optional[int] = None) -> BitrixObjectList["BaseDepartmentObject"]:
        """Подразделения по ID"""

        if department_ids:
            filter_dict = {"ID": list(department_ids)}
            return self.filter(
                filter_dict=filter_dict,
                order_dict=order_dict,
                select_only=select_only,
                select_related=select_related,
                timeout=timeout)
        else:
            return BitrixObjectList()

    @staticmethod
    def _validate_api_fields(api_data: Dict[Text, Text]) -> Dict[Text, Dict]:
        return {field_code: {"NAME": field_name} for field_code, field_name in api_data.items()}
