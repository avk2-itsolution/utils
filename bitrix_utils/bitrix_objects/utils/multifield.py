from typing import Optional, Text, Dict


class MultifieldObject:
    """Объект, описывающий «множественное поле».
    Множественные поля применяются для хранения телефонов, email-адресов и другой контактной информации.
    В лидах, контактах и компаниях полями этого типа являются PHONE, EMAIL, WEB, IM и LINK"""

    def __init__(self, *, value_type: Text, value: Text, bitrix_id: Optional[int] = None, type_id: Optional[Text] = None):
        self.bitrix_id = int(bitrix_id) if bitrix_id else None
        self.value_type = value_type
        self.value = value
        self.type_id = type_id

    @classmethod
    def from_dict(cls, bitrix_data: Dict[Text, Text]) -> "MultifieldObject":
        return cls(bitrix_id=bitrix_data.get("ID"),
                   value_type=bitrix_data["VALUE_TYPE"],
                   value=bitrix_data["VALUE"],
                   type_id=bitrix_data.get("TYPE_ID"))

    def to_dict(self) -> Dict[Text, Text]:
        return {"VALUE_TYPE": self.value_type, "VALUE": self.value}
