from utils.bitrix_utils.bitrix_objects.main import fields
from utils.bitrix_utils.bitrix_objects.main.bitrix_object import BitrixObject


class UserObject(BitrixObject):

    name = fields.TextBitrixField('NAME')

    # def __str__(self):
    #     return f"{self.bitrix_data['LAST_NAME']} {self.bitrix_data['NAME']}".strip()

    @property
    def bitrix_data(self):
        if not self._bitrix_data:
            self._bitrix_data = self.but.call_list_method('user.get', {'ID': self.bitrix_id})[0]
        return self._bitrix_data

    @property
    def url(self):
        return f"{self.portal_url}/company/personal/user/{self.bitrix_id}/"


    @classmethod
    def many_from_bitrix_api(cls, ids=None, but=None):
        #TODO Название туповатое, поменять бы
        users = []
        for u in but.call_list_method("user.get", {"ID": ids}):
            users.append(UserObject(u['ID'], but=but, bitrix_data=u))

        return users