from utils.bitrix_utils.bitrix_objects.crm.crm_object.crm_object_manager import CRMObjectManager
from utils.bitrix_utils.bitrix_objects.main.bitrix_object_list import BitrixObjectList

from typing import Type, TYPE_CHECKING, Text

if TYPE_CHECKING:
    from utils.bitrix_utils.bitrix_objects.crm import EnumObject


class EnumObjectManager(CRMObjectManager):
    """Менеджер enum-значений CRM.

    Examples:
        >>> EnumObject.objects(but).activity_types()
    """

    BITRIX_OBJECT_CLASS: Type["EnumObject"]

    def by_method(self, method: Text) -> BitrixObjectList["EnumObject"]:
        """Перечисления по методу"""
        enums = self.but.call_list_method(method)
        enum_objects = BitrixObjectList(self.BITRIX_OBJECT_CLASS(enum[self.BITRIX_OBJECT_CLASS.ID_FIELD_CODE], but=self.but, bitrix_data=enum) for enum in enums)
        return enum_objects

    def owner_types(self) -> BitrixObjectList["EnumObject"]:
        """Элементы перечисления «Тип владельца»"""
        return self.by_method("crm.enum.ownertype")

    def content_types(self) -> BitrixObjectList["EnumObject"]:
        """Элементы перечисления «Тип содержания»"""
        return self.by_method("crm.enum.contenttype")

    def activity_types(self) -> BitrixObjectList["EnumObject"]:
        """Элементы перечисления «Тип активности»"""
        return self.by_method("crm.enum.activitytype")

    def activivty_priorities(self) -> BitrixObjectList["EnumObject"]:
        """Элементы перечисления «Приоритет активности»"""
        return self.by_method("crm.enum.activitypriority")

    def activity_notify_types(self) -> BitrixObjectList["EnumObject"]:
        """Элементы перечисления «Тип уведомления о начале активности»"""
        return self.by_method("crm.enum.activitynotifytype")

    def address_types(self) -> BitrixObjectList["EnumObject"]:
        """Элементы перечисления «Тип адреса»"""
        return self.by_method("crm.enum.addresstype")

    def activity_statuses(self) -> BitrixObjectList["EnumObject"]:
        """Элементы перечисления «Статус»"""
        return self.by_method("crm.enum.activitystatus")

    def settings_modes(self) -> BitrixObjectList["EnumObject"]:
        """Элементы перечисления «Режимов работы CRM»"""
        return self.by_method("crm.enum.settings.mode")
