from typing import List, Dict

from utils.bitrix_utils.bitrix_objects.main.bitrix_object_manager import BitrixObjectManager
from utils.bitrix_utils.bitrix_objects.tasks.task_object import TaskObject
from integration_utils.iu_datetime.dt_its import DtIts


class TaskObjectManager(BitrixObjectManager):

    object_path = 'utils.bitrix_utils.bitrix_objects.task_object.TaskObject'

    def created_at_date(self, dt) -> List[TaskObject]:
        # Получить задача на заданную дату
        # from main_placement.classes.task_object_manager import TaskObjectManager
        # q = TaskObjectManager().created_at_date('2024-05-28')
        # q = TaskObjectManager().created_at_date(DtIts.now())
        # q = TaskObjectManager().created_at_date() на сегодня
        if type(dt) != DtIts:
            dt = DtIts.get(dt)

        start_time = dt.replace(hour=0, minute=0, second=0)
        end_time = dt.replace(hour=23, minute=59, second=59)
        return self.tasks_with_filter({"<=CREATED_DATE": end_time.bitrix_format(), ">CREATED_DATE": start_time.bitrix_format(), })

    def tasks_on_fired(self) -> List[TaskObject]:
        # TODO Можно сделать такой метод
        return []

    def tasks_with_filter(self, tasks_filter, verbose=True, title="Список задач") -> List[TaskObject]:
        # from main_placement.classes.task_object_manager import TaskObjectManager
        # TaskObjectManager().tasks_with_filter({"ALLOW_CHANGE_DEADLINE": "Y"}, verbose=True)
        # "<CREATED_DATE": date_365_days_ago,
        # "CREATED_BY": 1,
        # "!=RESPONSIBLE_ID": 1,
        # "ALLOW_CHANGE_DEADLINE": "Y",
        # "!=REAL_STATUS": 5,
        if not tasks_filter.get("!=REAL_STATUS") and not tasks_filter.get("REAL_STATUS"):
            # ПО умолчанию открыте задачи
            tasks_filter = tasks_filter.copy()
            tasks_filter['!=REAL_STATUS'] = 5
        tasks = self.but.call_list_method("tasks.task.list", {"filter": tasks_filter}, timeout=50)['tasks']
        tasks = [TaskObject(task['id'], bitrix_data=task) for task in tasks]
        if verbose:
            print(f"{title} количество {len(tasks)}")
            for task in tasks:
                print(task)

        return tasks

    def renew_or_create(self, tasks_filter: Dict) -> TaskObject:
        """Ищет (а если нет, то создает) задачу по названию и ответственному и переводит ее в статус новой"""

        tasks_filter.update({"REAL_STATUS": [1, 2, 3, 4, 5, 6, 7]})
        tasks = self.tasks_with_filter(tasks_filter)
        if len(tasks) == 0:
            # если нет задачи, то создаем
            tasks_filter.setdefault("RESPONSIBLE_ID", tasks_filter["CREATED_BY"])
            task = self.but.call_api_method("tasks.task.add", {"fields": tasks_filter})["result"]["task"]
            task_object = TaskObject(task["id"], bitrix_data=task)
        else:
            # иначе возобновляем
            task_object = tasks[-1]
            task_object.renew()

        return task_object

    def renew_or_create_by_title_and_group(self, title, group_id, to_responsible_id) -> TaskObject:
        """
        Ищет по title и group_id задачу
        Это значит что задача с определенным названиям может дубилроваться в разных проектах(группах)

        Если не находит задачи, то создает на ответственного указанного
        Если задача закрыта, то переоткрывает и переводит на указанного ответсвенного

        Если задача в работе, то ответсвенного не будет менять!!!!!
        """

        tasks_filter = {
            "TITLE": title,
            "GROUP_ID": group_id,
        }
        # Пытаемся найти открытые задачи
        tasks = self.tasks_with_filter(tasks_filter)

        if len(tasks) > 0:
            # Уже есть нужная задача
            return tasks[-1]

        # Если актиыных нет копаемся в завершенных
        tasks_filter.update({"REAL_STATUS": 5})
        tasks = self.tasks_with_filter(tasks_filter)

        if len(tasks) > 0:
            # иначе возобновляем
            task_object = tasks[-1]
            self.but.call_api_method('tasks.task.renew', {'taskId': task_object.id})
            # TODO надо сделать через TASKObject нормально
            self.but.call_api_method('tasks.task.update', {'taskId': task_object.id, 'fields': {"RESPONSIBLE_ID": to_responsible_id}})
            return task_object

        # если нет задачи, то создаем
        task = self.but.call_api_method("tasks.task.add", {"fields": {
            "TITLE": title,
            "GROUP_ID": group_id,
            "RESPONSIBLE_ID": to_responsible_id
        }})["result"]["task"]
        task_object = TaskObject(task["id"], bitrix_data=task)

        return task_object
