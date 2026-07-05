from utils.bitrix_utils.bitrix_objects.crm.lead_object import LeadObject
from utils.bitrix_utils.bitrix_objects.tasks.task_object_manager import TaskObjectManager
from utils.bitrix_utils.bitrix_objects.users.user_object import UserObject
from integration_utils.bitrix24.bitrix_token import BitrixToken
from integration_utils.bitrix24.models import BitrixUserToken

SECOND_USER_ID = 14806
THIRD_USER_ID = 20

webhook = "https://b24-n2wwl6.bitrix24.ru/rest/1/6mwuofwz7pxw7hzf/"
file_but = BitrixToken('b24-n2wwl6.bitrix24.ru', auth_token=None, web_hook_auth='1/6mwuofwz7pxw7hzf')


def lead_tests(but: BitrixUserToken = None):
    if not but:
        but = file_but

    user_object_55 = UserObject(55, but=but)
    print(UserObject(1, but=but))

    ww = user_object_55.name.value
    print(ww)

    q = UserObjectManager(but=evg_but).active_users().to_int()


    # Создаем задачу на юзера 1
    TaskObjectManager().renew_or_create()

    # Получаем все открытые задачи?
    res = TaskObjectManager(but).tasks_with_filter({})

    # USER_BITRIX_ID = but.user.bitrix_id
    #
    # # Инициализируем объект юзера с id = 1
    # user = UserObject(1, but)
    #
    # print(user) # Выводит фамилию и имя __str__ объекта
    # print(user.url) # Выводит ссылку на юзера в Битрикс24
    #
    #
    # # Создадим задачу для теста
    # t = but.call_api_method('tasks.task.add', {"fields": {"TITLE": "Тестовая задача", "RESPONSIBLE_ID": but.user.bitrix_id}})['result']['task']
    # created_task_id = t['id']
    #
    # task = TaskObject(created_task_id, but)
    # print("Создана задача " + task.url)
    #
    # # Проверяем добавление наблюдателя
    # TaskObject(created_task_id, but).add_auditor(SECOND_USER_ID)
    # TaskObject(created_task_id, but).add_auditor(THIRD_USER_ID)
    #
    # assert not set([SECOND_USER_ID, THIRD_USER_ID]) - set(TaskObject(created_task_id, but).auditors_ids)
    #
    #
    # # Проверяем смену ответсвенного
    # task.delegate(SECOND_USER_ID)
    #
    # assert int(TaskObject(created_task_id, but).responsible_id) == SECOND_USER_ID
    #
    #
