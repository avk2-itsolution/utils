from utils.bitrix_utils.bitrix_objects.main import fields
from utils.bitrix_utils.bitrix_objects.main.bitrix_object import BitrixObject
from utils.bitrix_utils.bitrix_objects.main.fields.bitrix_fields import TextBitrixField
from utils.bitrix_utils.bitrix_objects.tasks.group_object import GroupObject


class TaskObject(BitrixObject):

    title = TextBitrixField('TITLE', task_field_code='title')

    def __init__(self, id, but = None, bitrix_data = None):
        self.id = int(id)
        self.but = but
        self._bitrix_data = bitrix_data
        #self._group: GroupObject = None
        #self._rp_id = None

    def __str__(self):
        return f"{self.id} {self.bitrix_data['title']}"

    @property
    def url(self):
        return f"https://{self.but.user.portal.domain}/company/personal/user/{self.but.user.bitrix_id}/tasks/task/view/{self.id}/"

    @property
    def bitrix_data(self):
        if not self._bitrix_data:
            self._bitrix_data = self.but.call_list_method(
                'tasks.task.get',
                {'taskId': self.id})['task']
        return self._bitrix_data

    @property
    def responsible_id(self):
        return self.bitrix_data['responsibleId']

    @property
    def auditors_ids(self):
        return [int(x) for x in self.bitrix_data['auditors']]

    @property
    def accomplices_ids(self):
        return [int(x) for x in self.bitrix_data['accomplices']]

    @property
    def group(self):
        return GroupObject(self.bitrix_data['groupId'], self.but)

    def delegate(self, user_id):
        return self.but.call_api_method("tasks.task.delegate", {"taskId": self.id, "userId": user_id})

    def add_accomplice(self, user_id):
        return self.but.call_api_method("tasks.task.update", {"taskId": self.id,  "fields": {"ACCOMPLICES": self.accomplices_ids + [user_id]}})

    def add_auditor(self, user_id):
        return self.but.call_api_method("tasks.task.update", {"taskId": self.id,  "fields": {"AUDITORS": self.auditors_ids + [user_id]}})

    def update_field(self, field, value):
        # Обновляет поле задачи если оно прописано как FIELD_WITH_BALL
        task = self.but.call_api_method('tasks.task.update', {
            'taskId': self.id,
            'fields': {field: value}
        })['result']['task']
        # Обнулим значени _bitrix_data чтобы обновилось из АПИ при следующей выборке
        self._bitrix_data = None
        # TODO подумать здесь ли нужно обновление объекта? или вынести одельно?
        # if self._bitrix_data:
        #     self._bitrix_data.update(task)
        # if not task.get(field[1]):
        #     # Значит update не возвращает пользовательское поле
        #     # придется обновлять из API, можно было бы установить зная.. но на всякий случай лучше перечитать будет
        #     # self._bitrix_data[field[1]] = value
        #     self._bitrix_data = None
        return