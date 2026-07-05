from utils.bitrix_utils.bitrix_objects.crm.base_category_object.base_category_object import BaseCategoryObject


class BaseDealCategoryObject(BaseCategoryObject):
    """Воронка сделки.

    Обязательные параметры для создания/обновления (использует методы BaseCategoryObject):
    - entityTypeId: ``2`` (подставлен в классе).
    - name: название воронки.
    - sort/isDefault: порядок и флаг по умолчанию.
    """

    ENTITY_TYPE_ID = 2

    CRM_OBJECT = "utils.bitrix_utils.bitrix_objects.crm.BaseDealObject"
