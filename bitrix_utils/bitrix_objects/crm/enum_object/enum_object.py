from utils.bitrix_utils.bitrix_objects.crm.enum_object.enum_object_manager import EnumObjectManager
from utils.bitrix_utils.bitrix_objects.crm.crm_object import CRMObject
from utils.bitrix_utils.bitrix_objects.main.fields import TextBitrixField


class EnumObject(CRMObject):
    """Значение пользовательского поля (enum) CRM.

    Examples:
        >>> enums = EnumObject.objects(but).owner_types()
    """

    ENTITY_TYPE_NAME = "ENUM"
    USER_FIELD_ENTITY_ID = "CRM_ENUM"

    _objects = EnumObjectManager

    name = TextBitrixField("NAME", is_required=True)
    symbol_code = TextBitrixField("SYMBOL_CODE")
    symbol_code_short = TextBitrixField("SYMBOL_CODE_SHORT")

    def __str__(self):
        return self.name.value

    def __eq__(self, other: "EnumObject") -> bool:
        return self.bitrix_id == other.bitrix_id and self.name.value == other.name.value

    def __hash__(self) -> int:
        return hash((self.bitrix_id, self.name.value))
