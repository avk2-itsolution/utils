from utils.bitrix_utils.bitrix_objects.groups.base_group_object.base_group_object_manager import BaseGroupObjectManager
from utils.bitrix_utils.bitrix_objects.groups.constants import SELECT_FIELDS
from utils.bitrix_utils.bitrix_objects.main.bitrix_object_list import BitrixObjectList
from utils.bitrix_utils.bitrix_objects.main.bitrix_object import BitrixObject
from utils.bitrix_utils.bitrix_objects.main.fields.bitrix_fields import (
    IntBitrixField,
    TextBitrixField,
    DateTimeBitrixField,
    BoolBitrixField,
    DictBitrixField,
    ObjectBitrixField,
)

from typing import Dict, Text, Iterable, Optional, List


class BaseGroupObject(BitrixObject):
    """Группа Bitrix24 (workgroup/project) со стандартными полями и операциями.

    Examples:
        >>> group = BaseGroupObject.objects(but).get(bitrix_id=12)
        >>> group.add_user([42])
        >>> group.get_feature_access("tasks", "read")
        >>> group.url
    """

    ROLE_OWNER = 'A'
    ROLE_MODERATOR = 'E'
    ROLE_USER = 'K'

    USER_OBJECT = "utils.bitrix_utils.bitrix_objects.users.BaseUserObject"

    _objects = BaseGroupObjectManager

    name = TextBitrixField("NAME", is_required=True)
    description = TextBitrixField("DESCRIPTION")
    active = BoolBitrixField("ACTIVE", is_required=True)
    subject_id = IntBitrixField("SUBJECT_ID", is_required=True)
    subject_data = DictBitrixField("SUBJECT_DATA")
    keywords = TextBitrixField("KEYWORDS")
    closed = BoolBitrixField("CLOSED", is_required=True)
    visible = BoolBitrixField("VISIBLE", is_required=True)
    opened = BoolBitrixField("OPENED", is_required=True)
    project = BoolBitrixField('PROJECT', is_required=True)
    landing = BoolBitrixField("LANDING")
    date_create = DateTimeBitrixField("DATE_CREATE", is_required=True)
    date_update = DateTimeBitrixField("DATE_UPDATE", is_required=True)
    date_activity = DateTimeBitrixField("DATE_ACTIVITY", is_required=True)
    image_id = IntBitrixField("IMAGE_ID")
    avatar = TextBitrixField('AVATAR')
    avatar_type = TextBitrixField("AVATAR_TYPE")  # Тип аватара группы (используется, если не задано значение IMAGE_ID). Допустимые значения: folder, checks, pie, bag, members
    avatar_types = DictBitrixField("AVATAR_TYPES")
    owner = ObjectBitrixField("OWNER_ID", object_type=USER_OBJECT, is_required=True)
    owner_data = DictBitrixField("OWNER_DATA")
    number_of_members = IntBitrixField("NUMBER_OF_MEMBERS", is_required=True)
    number_of_moderators = IntBitrixField("NUMBER_OF_MODERATORS", is_required=True)
    initiate_perms = TextBitrixField("INITIATE_PERMS", is_required=True)  # Кто имеет право на приглашение пользователей в группу (обязательное поле): A - только владелец группы, E - владелец группы и модераторы группы, K - все члены группы
    search_index = TextBitrixField("SEARCH_INDEX")  # Строка с текстовым контентом группы (название, описание, владелец...)
    project_date_start = DateTimeBitrixField("PROJECT_DATE_START")
    project_date_end = DateTimeBitrixField("PROJECT_DATE_END")
    site_id = TextBitrixField('SITE_ID')
    scrum_owner_id = IntBitrixField("SCRUB_OWNER_ID")  # Идентификатор SCRUM
    scrum_master = ObjectBitrixField("SCRUB_MASTER_ID", object_type=USER_OBJECT)  # Идентификатор SCRUM мастера
    scrum_sprint_duration = IntBitrixField("SCRUB_DURATION")  # Длительность спринта в скраме в секундах
    scrum_task_responsible = TextBitrixField("SCRUB_TASK_RESPONSIBLE")  # Ответственный по умолчанию в скрам проекте
    type = TextBitrixField("TYPE")
    tags = TextBitrixField("TAGS", is_multiple=True)
    actions = DictBitrixField("ACTIONS")
    user_data = TextBitrixField("USER_DATA")
    uf_sg_dept = DictBitrixField("UF_SG_DEPT")

    def __str__(self):
        return self.name.value

    def _get_bitrix_data(self) -> Dict:
        result = self.but.call_api_method("socialnetwork.api.workgroup.get", {"params": {"groupId": self.bitrix_id, "select": SELECT_FIELDS}})["result"]
        return self._validate_api_get(result)

    def delete(self):
        """Удалить группу"""
        self.but.call_api_method("sonet_group.delete", {"GROUP_ID": self.bitrix_id})

    def update(self, fields: Dict):
        """Обновить группу"""
        self.but.call_api_method("sonet_group.update", {"GROUP_ID": self.bitrix_id} | fields)

    @property
    def url(self) -> Text:
        """Ссылка на группу"""
        return f"{self.portal_url}/workgroups/group/{self.bitrix_id}/"

    def get_feature_access(self, feature: Text, operation: Text) -> bool:
        """Проверить права текущего пользователя"""
        return self.but.call_api_method("sonet_group.feature.access", {"GROUP_ID": self.bitrix_id, "FEATURE": feature, "OPERATION": operation})["result"]

    def set_owner(self, user_id: int):
        """Изменить владельца группы"""
        self.but.call_api_method("sonet_group.setowner", {"GROUP_ID": self.bitrix_id, "USER_ID": user_id})

    def add_user(self, user_ids: Iterable[int]):
        """Добавить пользователей в группу"""
        self.but.call_api_method("sonet_group.user.add", {"GROUP_ID": self.bitrix_id, "USER_ID": list(user_ids)})

    def delete_user(self, user_ids: Iterable[int]):
        """Удалить пользователей из группы"""
        self.but.call_api_method("sonet_group.user.delete", {"GROUP_ID": self.bitrix_id, "USER_ID": list(user_ids)})

    @property
    def member_roles(self) -> Dict["USER_OBJECT", Text]:
        """Участники группы и их роли. Словарь вида: {user_object: роль}"""
        user_class = self.get_class(self.USER_OBJECT)
        users = self.but.call_list_method("sonet_group.user.get", {"ID": self.bitrix_id})
        return {user_class(user["USER_ID"], but=self.but): user["ROLE"] for user in users}

    @property
    def participants(self) -> BitrixObjectList["USER_OBJECT"]:
        """Участники"""
        return BitrixObjectList(self.member_roles.keys())

    def invite_user(self, user_ids: Iterable[int], message: Optional[Text] = None) -> List["USER_OBJECT"]:
        """Пригласить пользователей в группу, возвращает список пользователей, успешно приглашенных в группу"""
        user_class = self.get_class(self.USER_OBJECT)
        user_ids = self.but.call_list_method("sonet_group.user.invite", {"GROUP_ID": self.bitrix_id, "USER_ID": list(user_ids), "MESSAGE": message})
        return [user_class(user_id, but=self.but) for user_id in user_ids]

    def request_user(self, message: Text):
        """Отправить запрос на вступление в группу"""
        self.but.call_api_method("sonet_group.user.add", {"GROUP_ID": self.bitrix_id, "MESSAGE": message})

    def update_user(self, user_ids: Iterable[int], role: Text):
        """Изменить роль пользователя в группе"""
        self.but.call_api_method("sonet_group.user.update", {"GROUP_ID": self.bitrix_id, "USER_ID": list(user_ids), "ROLE": role})
