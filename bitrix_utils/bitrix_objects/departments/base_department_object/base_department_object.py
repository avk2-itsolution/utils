from utils.bitrix_utils.bitrix_objects.departments.base_department_object.base_department_object_manager import BaseDepartmentObjectManager
from utils.bitrix_utils.bitrix_objects.main import BitrixObject
from utils.bitrix_utils.bitrix_objects.main.exceptions import NotFoundObject
from utils.bitrix_utils.bitrix_objects.main.fields import (
    TextBitrixField,
    IntBitrixField,
    ObjectBitrixField,
)

from typing import Optional, Dict, List


class BaseDepartmentObject(BitrixObject):
    """Объект подразделения портала.

    Examples:
        >>> dep = BaseDepartmentObject.objects(but).get(bitrix_id=3)
        >>> dep.supervisor
        >>> dep.url
    """

    DEPARTMENT_OBJECT = "utils.bitrix_utils.bitrix_objects.departments.BaseDepartmentObject"
    USER_OBJECT = "utils.bitrix_utils.bitrix_objects.users.BaseUserObject"

    _objects = BaseDepartmentObjectManager

    name = TextBitrixField("NAME", is_required=True)
    parent = ObjectBitrixField("PARENT", object_type=DEPARTMENT_OBJECT)
    sort = IntBitrixField("SORT")
    uf_head = ObjectBitrixField("UF_HEAD", object_type=USER_OBJECT)

    def __str__(self):
        return self.name.value

    def _get_bitrix_data(self) -> Dict:
        result = self.but.call_api_method("department.get", {"ID": self.bitrix_id})["result"]
        return self._validate_api_get(result)

    def update(self, fields: Dict):
        """Обновить подразделение"""
        self.but.call_api_method("department.update", {"ID": self.bitrix_id, "fields": fields})

    def delete(self):
        """Удалить подразделение"""
        self.but.call_api_method("department.delete", {"ID": self.bitrix_id})

    @staticmethod
    def _validate_api_get(api_data: List) -> Dict:
        if api_data:
            return api_data[0]
        else:
            raise NotFoundObject("Подразделение не найдено на портале")

    @property
    def url(self):
        """Ссылка на подразделение"""
        return f"{self.portal_url}/company/structure.php?set_filter_structure=Y&structure_UF_DEPARTMENT={self.bitrix_id}"

    @property
    def supervisor(self) -> Optional["USER_OBJECT"]:
        """Получение первого непосредственного руководителя в дереве подразделений"""

        current_department = self

        while not current_department.uf_head.value and current_department.parent.value:
            # если не указан руководитель и есть родительсикй отдел
            current_department = current_department.parent.object

        return current_department.uf_head.object
