from utils.bitrix_utils.bitrix_objects.main.bitrix_object_manager import BitrixObjectManager
from utils.bitrix_utils.bitrix_objects.main.bitrix_object_list import BitrixObjectList

from typing import Dict, Iterable, Optional, List, Type, Any, TYPE_CHECKING, Text

if TYPE_CHECKING:
    from utils.bitrix_utils.bitrix_objects.tasks.base_task_object import BaseTaskObject


class BaseTaskObjectManager(BitrixObjectManager):
    """Менеджер задач Bitrix24.

    Examples:
        >>> tasks = BaseTaskObject.objects(but).filter({"RESPONSIBLE_ID": but.user_id})
        >>> all_tasks = BaseTaskObject.objects(but).all()
    """

    BITRIX_OBJECT_CLASS: Type["BaseTaskObject"]

    def get_fields(self) -> Dict:
        result = self.but.call_list_method("tasks.task.getFields")
        return self._validate_api_fields(result)

    def add(self, fields: Dict) -> int:
        """Создает задачу и возвращает ее ID.

        Обязательные параметры ``tasks.task.add``:
        - TITLE, название задачи
        - RESPONSIBLE_ID, идентификатор ответственного
        """
        result = self.but.call_api_method("tasks.task.add", {"fields": fields})["result"]
        return self._validate_api_add(result)

    def all(self,
            order_dict: Optional[Dict] = None,
            select_list: Optional[Iterable] = None,
            select_only: Optional[List[Text]] = None,
            select_related: Optional[List[Text]] = None,
            timeout: Optional[int] = None) -> BitrixObjectList["BaseTaskObject"]:
        """Все задачи"""
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
               select_list: Optional[Iterable] = None,
               select_only: Optional[List[Text]] = None,
               select_related: Optional[List[Text]] = None,
               timeout: Optional[int] = None) -> BitrixObjectList["BaseTaskObject"]:
        """Задачи по фильтру"""
        fields = {}

        if filter_dict:
            fields.update({"filter": filter_dict})

        if order_dict:
            fields.update({"order": order_dict})

        select_list = self.mix_select_list_and_select_only(select_list, select_only)

        if select_list:
            fields.update({"select": select_list})

        tasks = self.but.call_list_method("tasks.task.list", fields, timeout=timeout)
        tasks = self._validate_api_list(tasks)

        task_objects = BitrixObjectList(self.BITRIX_OBJECT_CLASS(task["id"], but=self.but, bitrix_data=task) for task in tasks)

        if select_related:
            self.set_select_related(task_objects, select_only=select_only, select_related=select_related)

        return task_objects

    def from_ids(self,
                 task_ids: Iterable[int],
                 order_dict: Optional[Dict] = None,
                 select_list: Optional[Iterable] = None,
                 select_only: Optional[List[Text]] = None,
                 select_related: Optional[List[Text]] = None,
                 timeout: Optional[int] = None) -> BitrixObjectList["BaseTaskObject"]:
        """Возвращает задачи по списку ID с теми же опциями выборки, что и ``filter``."""
        if task_ids:
            filter_dict = {"ID": list(task_ids)}
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
    def _validate_api_fields(api_data: Dict) -> Dict:
        """Поля приходят в UPPER_CASE, а не в camelCase"""

        def from_upper_to_camel(field_code: Text) -> Text:
            parts = field_code.lower().split('_')
            return parts[0] + ''.join(part.capitalize() for part in parts[1:])

        return {from_upper_to_camel(field_code): value for field_code, value in api_data["fields"].items()}

    @staticmethod
    def _validate_api_add(api_data: Dict) -> Any:
        return api_data["task"]["id"]

    @staticmethod
    def _validate_api_list(api_data: Dict) -> List:
        return api_data["tasks"]
