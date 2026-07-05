from utils.bitrix_utils.bitrix_objects.main import BitrixObject

from typing import Text, Optional, List, Dict, ForwardRef

BitrixUserToken = ForwardRef("BitrixUserToken")


class ContactBindingInterface:
    """Интерфейс для управления привязкой контактов"""

    CONTACT_OBJECT: Text

    bitrix_id: int
    but: BitrixUserToken
    entity_type: Text

    get_class = BitrixObject.get_class

    def add_contact(self, contact_id: int, sort: Optional[int] = None, is_primary: Optional[bool] = None):
        """Добавление привязки контакта к CRM-сущности"""
        self.but.call_api_method(f"crm.{self.entity_type}.contact.items.set", {
            "id": self.bitrix_id,
            "fields": {
                "CONTACT_ID": contact_id,
                "SORT": sort,
                "IS_PRIMARY": is_primary,
            }
        })

    def get_contacts(self) -> Dict["CONTACT_OBJECT", Dict]:
        """Возвращает привязанные контакты в качестве словаря вида:
        {contact_object: {"SORT": sort, "ROLE_ID": role_id, "IS_PRIMARY": is_primary}}"""

        contact_class = self.get_class(self.CONTACT_OBJECT)
        contact_items = self.but.call_list_method(f"crm.{self.entity_type}.contact.items.get", {"id": self.bitrix_id})
        return {contact_class(contact_item["CONTACT_ID"], but=self.but): {
            "SORT": contact_item["SORT"],
            "ROLE_ID": contact_item["ROLE_ID"],
            "IS_PRIMARY": contact_item["IS_PRIMARY"]
        } for contact_item in contact_items}

    def set_contacts(self, contact_items: List[Dict]):
        """Прикрепить список контактов к CRM-сущности"""
        self.but.call_list_method(f"crm.{self.entity_type}.contact.items.set", {"id": self.bitrix_id, "items": contact_items})

    def delete_contacts(self):
        """Удалить список контактов у CRM-сущности"""
        self.but.call_list_method(f"crm.{self.entity_type}.contact.items.delete", {"id": self.bitrix_id})

    def delete_contact(self, contact_id: int):
        """Удаление привязки контакта к CRM-сущности"""
        self.but.call_api_method(f"crm.{self.entity_type}.contact.delete", {"id": self.bitrix_id, "fields": {"CONTACT_ID": contact_id}})
