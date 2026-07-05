from utils.bitrix_utils.bitrix_objects.users.base_user_object.base_user_object_manager import BaseUserObjectManager
from utils.bitrix_utils.bitrix_objects.main.bitrix_object_list import BitrixObjectList
from utils.bitrix_utils.bitrix_objects.departments.base_department_object.base_department_object import BaseDepartmentObject
from utils.bitrix_utils.bitrix_objects.main import BitrixObject
from utils.bitrix_utils.bitrix_objects.main.fields import (
    TextBitrixField,
    BoolBitrixField,
    DateTimeBitrixField,
    DictBitrixField,
    ObjectBitrixField,
)

from typing import Dict, Text, Optional


class BaseUserObject(BitrixObject):
    """Пользователь портала (готовый класс).

    Examples:
        >>> user = BaseUserObject.objects(but).get(bitrix_id=42)
        >>> user.email.value
        >>> user.uf_department.objects  # связанные отделы
    """

    TYPE_EMPLOYEE = "employee"
    TYPE_EXTRANET = "extranet"
    TYPE_EMAIL = "email"

    USER_OBJECT = "utils.bitrix_utils.bitrix_objects.users.BaseUserObject"
    DEPARTMENT_OBJECT = "utils.bitrix_utils.bitrix_objects.departments.BaseDepartmentObject"

    _objects = BaseUserObjectManager

    name = TextBitrixField("NAME")
    last_name = TextBitrixField("LAST_NAME")
    second_name = TextBitrixField("SECOND_NAME")
    personal_photo = TextBitrixField("PERSONAL_PHOTO")
    personal_birthday = DateTimeBitrixField("PERSONAL_BIRTHDAY")
    personal_gender = TextBitrixField("PERSONAL_GENDER")
    personal_city = TextBitrixField("PERSONAL_CITY")
    personal_mobile = TextBitrixField("PERSONAL_MOBILE")
    personal_www = TextBitrixField("PERSONAL_WWW")
    active = BoolBitrixField("ACTIVE", is_required=True)
    email = TextBitrixField("EMAIL")
    xml_id = TextBitrixField("XML_ID")
    date_register = DateTimeBitrixField("DATE_REGISTER", is_required=True)
    last_login = DateTimeBitrixField("LAST_LOGIN")
    last_activity_date = DictBitrixField("LAST_ACTIVITY_DATE")
    is_online = BoolBitrixField("IS_ONLINE", is_required=True)
    time_zone = TextBitrixField("TIME_ZONE")
    time_zone_offset = TextBitrixField("TIME_ZONE_OFFSET")
    timestamp_x = DictBitrixField("TIMESTAMP_X")
    work_phone = TextBitrixField("WORK_PHONE")
    work_position = TextBitrixField("WORK_POSITION")
    uf_skype_link = TextBitrixField("UF_SKYPE_LINK")
    uf_zoom = TextBitrixField("UF_ZOOM")
    uf_employment_date = DateTimeBitrixField("UF_EMPLOYMENT_DATE")
    uf_department = ObjectBitrixField("UF_DEPARTMENT", object_type=DEPARTMENT_OBJECT, is_multiple=True)
    uf_interests = TextBitrixField("UF_INTERESTS")
    uf_skills = TextBitrixField("UF_SKILLS")
    uf_web_sites = TextBitrixField("UF_WEB_SITES")
    uf_xing = TextBitrixField("UF_XING")
    uf_linkedin = TextBitrixField("UF_LINKEDIN")
    uf_facebook = TextBitrixField("UF_FACEBOOK")
    uf_twitter = TextBitrixField("UF_TWITTER")
    uf_skype = TextBitrixField("UF_SKYPE")
    uf_district = TextBitrixField("UF_DISTRICT")
    uf_phone_inner = TextBitrixField("UF_PHONE_INNER")
    uf_timeman = TextBitrixField("UF_TIMEMAN")
    title = TextBitrixField("TITLE")
    user_type = TextBitrixField("USER_TYPE")
    personal_country = TextBitrixField("PERSONAL_COUNTRY")
    personal_zip = TextBitrixField("PERSONAL_ZIP")
    personal_state = TextBitrixField("PERSONAL_STATE")
    personal_street = TextBitrixField("PERSONAL_STREET")
    personal_phone = TextBitrixField("PERSONAL_PHONE")
    personal_fax = TextBitrixField("PERSONAL_FAX")
    personal_pager = TextBitrixField("PERSONAL_PAGER")
    personal_icq = TextBitrixField("PERSONAL_ICQ")
    personal_mailbox = TextBitrixField("PERSONAL_MAILBOX")
    personal_profession = TextBitrixField("PERSONAL_PROFESSION")
    personal_notes = TextBitrixField("PERSONAL_NOTES")
    work_company = TextBitrixField("WORK_COMPANY")
    work_department = TextBitrixField("WORK_DEPARTMENT")
    work_www = TextBitrixField("WORK_WWW")
    work_fax = TextBitrixField("WORK_FAX")
    work_pager = TextBitrixField("WORK_PAGER")
    work_street = TextBitrixField("WORK_STREET")
    work_mailbox = TextBitrixField("WORK_MAILBOX")
    work_country = TextBitrixField("WORK_COUNTRY")
    work_zip = TextBitrixField("WORK_ZIP")
    work_state = TextBitrixField("WORK_STATE")
    work_city = TextBitrixField("WORK_CITY")
    work_logo = TextBitrixField("WORK_LOGO")
    work_notes = TextBitrixField("WORK_NOTES")
    work_profile = TextBitrixField("WORK_PROFILE")

    def __str__(self):
        last_name = self.last_name.value or ""
        name = self.name.value or ""
        second_name = self.second_name.value or ""
        return f"{last_name} {name} {second_name}".strip()

    def _get_bitrix_data(self) -> Dict:
        result = self.but.call_api_method("user.get", {"ID": self.bitrix_id, "ADMIN_MODE": True})["result"][0]
        return self._validate_api_get(result)

    def update(self, fields: Dict):
        """Обновить элемент"""
        self.but.call_api_method("user.update", {"ID": self.bitrix_id} | fields)

    @property
    def url(self) -> Text:
        """Ссылка на элемент списка"""
        return f"{self.portal_url}/company/personal/user/{self.bitrix_id}/"

    @property
    def supervisors(self) -> BitrixObjectList["USER_OBJECT"]:
        """Все непосредственные руководители пользователя"""
        department_class = self.get_class(self.DEPARTMENT_OBJECT)
        user_departments = department_class.objects(self.but).from_ids(self.uf_department.value, select_related=["uf_head"])
        return BitrixObjectList(user_department.uf_head.object for user_department in user_departments if user_department.uf_head.value)

    @property
    def supervisor(self) -> Optional["USER_OBJECT"]:
        """Получение одного руководителя"""

        department_class = self.get_class(self.DEPARTMENT_OBJECT)
        user_departments = department_class.objects(self.but).from_ids(self.uf_department.value, select_related=["uf_head"])

        # сначала попробуем найти непосредственного руководителя подразделения
        for user_department in user_departments:
            if user_department.uf_head.value:
                return user_department.uf_head.object

        if user_departments:
            # Так как у подразделения может не быть руководителя, то получаем следующего и т.д.
            return user_departments[0].supervisor
        else:
            return None
