from utils.bitrix_utils.bitrix_objects.crm.crm_object.crm_object_manager import CRMObjectManager
from utils.bitrix_utils.bitrix_objects.main.bitrix_object_list import BitrixObjectList

from typing import Type, TYPE_CHECKING, Dict, List, Text, Any, Tuple

if TYPE_CHECKING:
    from utils.bitrix_utils.bitrix_objects.crm.base_productrow_object import BaseProductRowObject


class BaseProductRowObjectManager(CRMObjectManager):
    """Менеджер товарных позиций CRM.

    Examples:
        >>> rows = BaseProductRowObject.objects(but).get_by_item(owner_id=501, owner_type="D")
    """

    BITRIX_OBJECT_CLASS: Type["BaseProductRowObject"]

    def set_by_item(self, owner_id: int, owner_type: Text, product_rows_data: List[Dict[Text, Any]]) -> BitrixObjectList["BITRIX_OBJECT_CLASS"]:
        """Установить товарные позиции (``crm.item.productrow.set``).
        https://apidocs.bitrix24.ru/api-reference/crm/universal/product-rows/crm-item-productrow-set.html

        Обязательные параметры:
        - ownerId: ID элемента.
        - ownerType: код сущности (например, ``D`` или ``Txx``).
        - productRows: список словарей (productId/productName, price, quantity, discount и т.п.).
        """

        if product_rows_data:
            product_rows = self.but.call_list_method("crm.item.productrow.set", {"ownerId": owner_id, "ownerType": owner_type, "productRows": product_rows_data})
            product_rows = self._validate_api_list(product_rows)
            return BitrixObjectList(self.BITRIX_OBJECT_CLASS(product_row[self.BITRIX_OBJECT_CLASS.ID_FIELD_CODE], but=self.but, bitrix_data=product_row) for product_row in product_rows)
        else:
            # метод crm.item.productrow.set не поддеживает установку пустого списка товаров

            methods: List[Tuple] = []

            for product_row_object in self.get_by_item(owner_id=owner_id, owner_type=owner_type):
                methods.append((product_row_object.bitrix_id, f"crm.{self.entity_type}.delete", {"entityTypeId": self.BITRIX_OBJECT_CLASS.ENTITY_TYPE_ID, "id": product_row_object.bitrix_id}))

            self.but.batch_api_call(methods)

            return BitrixObjectList()

    def get_by_item(self, owner_id: int, owner_type: Text, **kwargs) -> BitrixObjectList["BITRIX_OBJECT_CLASS"]:
        """Товарные позиции для конкретной CRM-сущности (``crm.item.productrow.list``).
        https://apidocs.bitrix24.ru/api-reference/crm/universal/product-rows/crm-item-productrow-list.html

        Обязательные параметры:
        - ownerId: ID элемента.
        - ownerType: код сущности.
        """
        filter_dict = {"=ownerId": owner_id, "=ownerType": owner_type}
        return self.filter(filter_dict, **kwargs)

    @staticmethod
    def _validate_api_add(api_data: Dict) -> int:
        return api_data["productRow"]["id"]

    @staticmethod
    def _validate_api_list(api_data: Dict) -> List:
        return api_data["productRows"]

    @staticmethod
    def _validate_api_fields(api_data: Dict) -> Dict:
        return api_data["fields"]
