from utils.bitrix_utils.bitrix_objects.main.bitrix_object_manager import BitrixObjectManager
from utils.bitrix_utils.bitrix_objects.main.response_list import ResponseList


class UserObjectManager(BitrixObjectManager):

    object_path = 'utils.bitrix_utils.bitrix_objects.user_object.UserObject'

    def active_users(self):
        return ResponseList(self.but.call_list_method("user.get", {"filter": {"ACTIVE": True}}))


