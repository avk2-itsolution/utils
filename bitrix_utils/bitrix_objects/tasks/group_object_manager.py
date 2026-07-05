from utils.bitrix_utils.bitrix_objects.main.bitrix_object_manager import BitrixObjectManager
from utils.bitrix_utils.bitrix_objects.main.response_list import ResponseList


class GroupObjectManager(BitrixObjectManager):

    object_path = 'utils.bitrix_utils.bitrix_objects.group_object.GroupObject'

    def get_all(self):
        groups = self.but.call_list_method('sonet_group.get', {'IS_ADMIN': 'Y'})
        return ResponseList(groups)


    def with_filter(self, filter):
        groups = self.but.call_list_method('sonet_group.get', {'FILTER': filter, 'IS_ADMIN': 'Y'})
        return ResponseList(groups)