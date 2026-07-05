from utils.bitrix_utils.bitrix_objects.main import BitrixObject

from typing import Text, Optional, List, Dict, ForwardRef

BitrixUserToken = ForwardRef("BitrixUserToken")


class CompanyBindingInterface:
    """Интерфейс для управления привязкой компаний"""

    COMPANY_OBJECT: Text

    bitrix_id: int
    but: BitrixUserToken
    entity_type: Text

    get_class = BitrixObject.get_class

    def add_company(self, company_id: int, sort: Optional[int] = None, is_primary: Optional[bool] = None):
        """Добавление привязки компании к контакту"""
        self.but.call_api_method("crm.contact.company.add", {
            "id": self.bitrix_id,
            "fields": {
                "COMPANY_ID": company_id,
                "SORT": sort,
                "IS_PRIMARY": is_primary,
            }
        })

    def get_companies(self) -> Dict["COMPANY_OBJECT", Dict]:
        """Возвращает привязанные компании в качестве словаря вида:
        {company_object: {"SORT": sort, "ROLE_ID": role_id, "IS_PRIMARY": is_primary}}"""

        company_class = self.get_class(self.COMPANY_OBJECT)
        company_items = self.but.call_list_method("crm.contact.company.items.get", {"id": self.bitrix_id})
        return {company_class(company_item["COMPANY_ID"], but=self.but): {
            "SORT": company_item["SORT"],
            "ROLE_ID": company_item["ROLE_ID"],
            "IS_PRIMARY": company_item["IS_PRIMARY"]
        } for company_item in company_items}

    def set_companies(self, company_items: List[Dict]):
        """Прикрепить список компаний к контакту"""
        self.but.call_list_method("crm.contact.company.items.set", {"id": self.bitrix_id, "items": company_items})

    def delete_companies(self):
        """Удалить список компаний у контакта"""
        self.but.call_list_method("crm.contact.company.items.delete", {"id": self.bitrix_id})

    def delete_company(self, company_id: int):
        """Удаление привязки компании к контакту"""
        self.but.call_api_method("crm.contact.company.delete", {"id": self.bitrix_id, "fields": {"COMPANY_ID": company_id}})
