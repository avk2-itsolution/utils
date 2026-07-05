import datetime

from django.utils.functional import classproperty

from utils.bitrix_utils.bitrix_objects.main import BitrixObject
from utils.bitrix_utils.bitrix_objects.main.bitrix_object_list import BitrixObjectList
from utils.bitrix_utils.bitrix_objects.crm.crm_object.crm_object_manager import CRMObjectManager

from typing import Dict, Text, List, Any, Type, Optional


class CRMObject(BitrixObject):
    """Базовый класс для CRM-сущности.

    Examples:
        Наследование для сущности (обязательны ENTITY_TYPE_ID/NAME/ABBR):
            class Deal(CRMObject):
                ENTITY_TYPE_ID = 2
                ENTITY_TYPE_NAME = "deal"
                ENTITY_TYPE_ABBR = "D"
                USER_FIELD_ENTITY_ID = "CRM_DEAL"
    """

    ENTITY_TYPE_ID: int = NotImplementedError
    ENTITY_TYPE_NAME: Text = NotImplementedError
    ENTITY_TYPE_ABBR: Text = NotImplementedError
    USER_FIELD_ENTITY_ID: Text = NotImplementedError

    CATEGORY_OBJECT = "utils.bitrix_utils.bitrix_objects.crm.BaseCategoryObject"
    PRODUCT_ROW_OBJECT = "utils.bitrix_utils.bitrix_objects.crm.BaseProductRowObject"
    TASK_OBJECT = "utils.bitrix_utils.bitrix_objects.tasks.BaseTaskObject"
    ACTIVITY_OBJECT = "utils.bitrix_utils.bitrix_objects.crm.base_activity_object.BaseActivityObject"

    _objects = CRMObjectManager

    # воронки для текущей crm-сущности
    _categories: Optional[BitrixObjectList["CATEGORY_OBJECT"]] = None

    def _get_bitrix_data(self) -> Dict:
        result = self.but.call_api_method(self._get_method, {"entityTypeId": self.ENTITY_TYPE_ID, "id": self.bitrix_id})["result"]
        return self._validate_api_get(result)

    def update(self, fields: Dict):
        """Обновить элемент"""
        self.but.call_api_method(self._update_method, {"entityTypeId": self.ENTITY_TYPE_ID, "id": self.bitrix_id, "fields": fields})

    def delete(self):
        """Удалить элемент"""
        self.but.call_api_method(self._delete_method, {"entityTypeId": self.ENTITY_TYPE_ID, "id": self.bitrix_id})

    @property
    def is_exist(self) -> bool:
        """Существует ли CRM-объект в Битриксе"""
        from integration_utils.bitrix24.exceptions import BitrixApiError

        try:
            self.bitrix_data
        except BitrixApiError as exc:
            if exc.is_not_found or exc.error == "NOT_FOUND":
                return False
            raise
        return True

    def __bool__(self) -> bool:
        return self.is_exist

    def get_product_rows(self, **kwargs) -> BitrixObjectList["PRODUCT_ROW_OBJECT"]:
        """Получить товарные позиции"""
        product_row_class = self.get_class(self.PRODUCT_ROW_OBJECT)
        return product_row_class.objects(self.but).get_by_item(owner_id=self.bitrix_id, owner_type=self.ENTITY_TYPE_ABBR, **kwargs)

    def set_product_rows(self, product_rows_data: List[Dict[Text, Any]]) -> BitrixObjectList["PRODUCT_ROW_OBJECT"]:
        """Устанавливает товарные позиции элемента CRM.

        - productRows: список словарей (productId/productName, price, quantity, discount, measure и т.п.).

        """
        product_row_class = self.get_class(self.PRODUCT_ROW_OBJECT)
        return product_row_class.objects(self.but).set_by_item(owner_id=self.bitrix_id, owner_type=self.ENTITY_TYPE_ABBR, product_rows_data=product_rows_data)

    def create_task(self, fields: Dict) -> "TASK_OBJECT":
        """Создает задачу, связывая ее с текущей CRM-сущностью.

        Обязательные параметры ``tasks.task.add``:
        - TITLE: заголовок задачи.
        - RESPONSIBLE_ID: ID ответственного.
        - UF_CRM_TASK: привязка к CRM (добавляется автоматически как ``[uf_crm]``).

        Returns:
            TASK_OBJECT: Созданная задача.
        """
        task_class = self.get_class(self.TASK_OBJECT)
        return task_class.objects(self.but).create(fields | {task_class.uf_crm_task.field_code_to_bitrix: [self.uf_crm]})

    def add_timeline_comment(self, comment: str, author_id: int) -> int:
        """
        Добавляет комментарий к смарт-элементу через API timeline.
        Возвращает ID созданного комментария.

        Использует REST-метод crm.timeline.comment.add.
        Обязательные параметры (внутри fields):
        - ENTITY_TYPE_ID: числовой ID типа смарт-процесса
        - ENTITY_ID: ID элемента смарт-процесса
        - COMMENT: текст комментария
        - AUTHOR_ID: ID пользователя, от имени которого создаётся комментарий

        пример использования:
        com = crm_object.add_comment(comment="Изучил материал", author_id=but.user_id)
        """
        return self.but.call_api_method(
            "crm.timeline.comment.add",
            {
                "fields": {
                    "ENTITY_ID": self.bitrix_id,
                    "ENTITY_TYPE": self.ENTITY_TYPE_NAME,
                    "AUTHOR_ID": author_id,
                    "COMMENT": comment,
                },
            },
        )["result"]

    def create_todo(self, deadline: datetime.datetime, title: Optional[str] = None, responsible_id: Optional[int] = None, description: Optional[str] = None) -> int:
        """
        Создает универсальное дело

        Пример запроса:
            act = crm_object.create_todo(title="Создать аккаунт в приложении",deadline=datetime.datetime.now()+datetime.timedelta(days=1), responsible_id=but.user_id,)
        """
        response = self.but.call_api_method(
            "crm.activity.todo.add",
            {
                'ownerTypeId': self.ENTITY_TYPE_ID,
                'ownerId': self.bitrix_id,
                "deadline": deadline.isoformat(),
                "title": title,
                "description": description,
                "responsibleId": responsible_id,
            }
        )
        return response["result"]

    def create_activity(self, fields: Dict) -> "ACTIVITY_OBJECT":
        """
        Создать дело (activity) для текущего CRM-объекта.
        Возвращает BaseActivityObject.

        Обязательные параметры для метода crm.activity.add:

        1. SUBJECT — тема дела (строка)
        2. TYPE_ID — тип активности (целое число, например 1 — задание, 2 — звонок)
        3. COMPLETED — статус ("Y" или "N")
        4. RESPONSIBLE_ID — ID ответственного пользователя
        5. BINDINGS — список привязок к CRM-объектам, например:
           [{"OWNER_ID": 123, "OWNER_TYPE_ID": 31}]

        Иногда также требуются в зависимости от активности:
        - PROVIDER_ID и PROVIDER_TYPE_ID — например "CRM_TASK" / "TASK"
        - COMMUNICATIONS — список контактов, если это звонок или письмо
        - DIRECTION — направление (1 — исходящее, 2 — входящее)

        Пример минимального запроса:
        fields = {
            "SUBJECT": "Тема дела",
            "TYPE_ID": 1,
            "COMPLETED": "N",
            "RESPONSIBLE_ID": but.user_id,
        }


        """
        activity_class = self.get_class(self.ACTIVITY_OBJECT)

        fields = fields | {
            "OWNER_ID": self.bitrix_id,
            "OWNER_TYPE_ID": self.ENTITY_TYPE_ID
        }

        return activity_class.objects(self.but).create(fields)

    @classproperty
    def category_class(cls) -> Type["CATEGORY_OBJECT"]:
        """Класс воронки в зависимости от ENTITY_TYPE_ID"""

        category_class = cls.get_class(cls.CATEGORY_OBJECT)

        class CategoryObject(category_class):
            ENTITY_TYPE_ID = cls.ENTITY_TYPE_ID
            CRM_OBJECT = cls

        return CategoryObject

    @property
    def categories(self) -> BitrixObjectList["CATEGORY_OBJECT"]:
        """Воронки для текущей CRM-сущности"""
        if self._categories is None:
            self.__class__._categories = self.objects(self.but).get_categories()
        return self._categories

    @classproperty
    def entity_type(cls) -> Text:
        """Тип CRM-сущности"""
        return cls.ENTITY_TYPE_NAME.lower()

    @classproperty
    def _get_method(cls) -> Text:
        return f"crm.{cls.entity_type}.get"

    @classproperty
    def _update_method(cls) -> Text:
        return f"crm.{cls.entity_type}.update"

    @classproperty
    def _delete_method(cls) -> Text:
        return f"crm.{cls.entity_type}.delete"

    @property
    def is_smart_process(self) -> bool:
        """Является ли смарт-процессом"""
        return self.entity_type == "item"

    @property
    def uf_crm(self) -> Text:
        """L_XX - лид, C_XX - контакт, D_XX - сделка, TXX_XX - смарт-процесс"""
        return f"{self.ENTITY_TYPE_ABBR}_{self.bitrix_id}"

    @property
    def url(self) -> Text:
        """Ссылка на CRM-сущность"""
        return f"{self.portal_url}/crm/{self.entity_type}/details/{self.bitrix_id}/"
