from utils.bitrix_utils.bitrix_auth.models import BitrixUserToken
from utils.bitrix_utils.bitrix_objects.tasks.task_object import TaskObject
from utils.bitrix_utils.bitrix_objects.users.user_object import UserObject

SECOND_USER_ID = 14806
THIRD_USER_ID = 20

"""
Ручной прогон

from utils.bitrix_utils.bitrix_objects.user_object import UserObject
from integration_utils.bitrix24.bitrix_token import BitrixToken
#https://b24-se4463.bitrix24.ru/devops/edit/in-hook/4/
#https://b24-se4463.bitrix24.ru/devops/list/
webhook = "https://b24-se4463.bitrix24.ru/rest/1/znv2jlxb641y002b/"
but = BitrixToken('b24-se4463.bitrix24.ru', auth_token=None, web_hook_auth='1/znv2jlxb641y002b')

# Проверяем работу UserObject
user = UserObject(1, but=but)
print(user.name.value)

# Проверяем работу UserObjectManager
from utils.bitrix_utils.bitrix_objects.user_object_manager import UserObjectManager
users = UserObjectManager(but).from_ids_list([1,2,6,8])


from utils.bitrix_utils.bitrix_objects.tasks.task_object import TaskObject
title = TaskObject(1, but=but).title.value
print(title)

TaskObject(1, but=but).title.set_value(title+" !")


"""


def test(but: BitrixUserToken):
    USER_BITRIX_ID = but.user.bitrix_id

    # Инициализируем объект юзера с id = 1
    user = UserObject(1, but)

    print(user) # Выводит фамилию и имя __str__ объекта
    print(user.url) # Выводит ссылку на юзера в Битрикс24


    # Создадим задачу для теста
    t = but.call_api_method('tasks.task.add', {"fields": {"TITLE": "Тестовая задача", "RESPONSIBLE_ID": but.user.bitrix_id}})['result']['task']
    created_task_id = t['id']

    task = TaskObject(created_task_id, but)
    print("Создана задача " + task.url)

    # Проверяем добавление наблюдателя
    TaskObject(created_task_id, but).add_auditor(SECOND_USER_ID)
    TaskObject(created_task_id, but).add_auditor(THIRD_USER_ID)

    assert not set([SECOND_USER_ID, THIRD_USER_ID]) - set(TaskObject(created_task_id, but).auditors_ids)


    # Проверяем смену ответсвенного
    task.delegate(SECOND_USER_ID)

    assert int(TaskObject(created_task_id, but).responsible_id) == SECOND_USER_ID


