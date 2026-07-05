from utils.bitrix_utils.bitrix_objects.main.bitrix_object import BitrixObject
from utils.bitrix_utils.bitrix_objects.tasks.group_object_manager import GroupObjectManager


class GroupObject(BitrixObject):
    """
    Объект группы
    https://dev.1c-bitrix.ru/rest_help/sonet_group/sonet_group_get.php
    """

    _objects = GroupObjectManager

    # def __init__(self, id, but: BitrixUserToken=None):
    #     self.bitrix_id = int(id)
    #     self.but: BitrixUserToken = but
    #     self._bitrix_data = None

    def __str__(self):
        return f"{self.bitrix_id} {self.bitrix_data['NAME']}"

    @property
    def url(self):
        return f"https://{self.but.user.portal.domain}/workgroups/group/{self.bitrix_id}/"

    def _get_bitrix_data(self):
        result = self.but.call_list_method('sonet_group.get', {'FILTER': {'ID': self.bitrix_id}, 'IS_ADMIN': 'Y'})[0]
        return result


    @property
    def participants(self):
        # Возвращает id участников и их роли
        #[{'USER_ID': '1', 'ROLE': 'A'}, {'USER_ID': '2905', 'ROLE': 'E'}, {'USER_ID': '7034', 'ROLE': 'K'}, {'USER_ID': '4', 'ROLE': 'K'}, {'USER_ID': '9273', 'ROLE': 'K'}, {'USER_ID': '8', 'ROLE': 'K'}, {'USER_ID': '12946', 'ROLE': 'K'}, {'USER_ID': '13143', 'ROLE': 'K'}]
        return self.but.call_list_method("sonet_group.user.get", {"ID": self.bitrix_id})

    @property
    def participants_id(self):
        return [group_participant["USER_ID"] for group_participant in self.participants]


    def participants_with_userdata(self):
        # Возвращает id участников и их роли
        #[{'USER_ID': '1', 'ROLE': 'A'}, {'USER_ID': '2905', 'ROLE': 'E'}, {'USER_ID': '7034', 'ROLE': 'K'}, {'USER_ID': '4', 'ROLE': 'K'}, {'USER_ID': '9273', 'ROLE': 'K'}, {'USER_ID': '8', 'ROLE': 'K'}, {'USER_ID': '12946', 'ROLE': 'K'}, {'USER_ID': '13143', 'ROLE': 'K'}]
        return self.but.call_list_method("sonet_group.user.get", {"ID": self.bitrix_id})

    def change_owner(self, user_id):
        return self.but.call_api_method('sonet_group.setowner', {'GROUP_ID': self.bitrix_id, 'USER_ID': user_id, 'ADMIN_MODE': True})


    def update_field(self, field, value):
        # Это нужно переопределить, т.к. разные методы вызватся tasks.task.update или crm.deal.update
        # В слушчае с tasks результат апдейта возвращает поля задачи новые..., но с пользоватльскими есть нюанс, можно использовать логику для оптимизации количества запросов
        # TODO доделать
        task = self.but.call_api_method('sonet_group.update', {
            'GROUP_ID': self.bitrix_id,
            'fields': {field[0]: value}
        })['result']['task']
        self._bitrix_data = None

