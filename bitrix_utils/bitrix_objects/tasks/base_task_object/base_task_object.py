from utils.bitrix_utils.bitrix_objects.tasks.base_task_object.base_task_object_manager import BaseTaskObjectManager
from utils.bitrix_utils.bitrix_objects.main.exceptions import NotFoundObject
from utils.bitrix_utils.bitrix_objects.main.bitrix_object import BitrixObject
from utils.bitrix_utils.bitrix_objects.main.fields import (
    TextBitrixField,
    IntBitrixField,
    BoolBitrixField,
    EnumBitrixField,
    DateTimeBitrixField,
    FloatBitrixField,
    ObjectBitrixField,
)

from typing import Dict, Text, Iterable


class BaseTaskObject(BitrixObject):
    """Базовый класс задачи Bitrix24.

    # Передвинуть финиш на завтра
    task_object.end_date_plan.value = DtIts.now().shift(days=days)
    task_object.save()

    """

    ID_FIELD_CODE = "id"

    STATE_NEW = '1'
    STATE_PENDING = '2'
    STATE_IN_PROGRESS = '3'
    STATE_SUPPOSEDLY_COMPLETED = '4'
    STATE_COMPLETED = '5'
    STATE_DEFERRED = '6'
    STATE_DECLINED = '7'

    STATE_ALMOST_EXPIRED = '-3'
    STATE_NOT_VIEWED = '-2'
    STATE_EXPIRED = '-1'

    GROUP_OBJECT = "utils.bitrix_utils.bitrix_objects.groups.BaseGroupObject"
    USER_OBJECT = "utils.bitrix_utils.bitrix_objects.users.BaseUserObject"

    _objects = BaseTaskObjectManager

    title = TextBitrixField("title", is_required=True, field_code_to_bitrix="TITLE")
    parent_id = IntBitrixField("parentId", field_code_to_bitrix="PARENT_ID")
    description = TextBitrixField("description", field_code_to_bitrix="DESCRIPTION")
    mark = BoolBitrixField("mark", field_code_to_bitrix="MARK")
    priority = EnumBitrixField("priority", is_required=True, field_code_to_bitrix="PRIORITY")
    status = EnumBitrixField("status", is_required=True, field_code_to_bitrix="STATUS")
    multitask = BoolBitrixField("multitask", is_required=True, field_code_to_bitrix="MULTITASK")
    not_viewed = BoolBitrixField("notViewed", field_code_to_bitrix="NOT_VIEWED")
    replicate = BoolBitrixField("replicate", field_code_to_bitrix="REPLICATE")
    group = ObjectBitrixField("groupId", object_type=GROUP_OBJECT, is_required=True, field_code_to_bitrix="GROUP_ID")
    stage_id = IntBitrixField("stageId", is_required=True, field_code_to_bitrix="STAGE_ID")
    created_by = ObjectBitrixField("createdBy", object_type=USER_OBJECT, is_required=True, field_code_to_bitrix="CREATED_BY")
    created_date = DateTimeBitrixField("createdDate", is_required=True, field_code_to_bitrix="CREATED_DATE")
    responsible_id = ObjectBitrixField("responsibleId", object_type=USER_OBJECT, is_required=True, field_code_to_bitrix="RESPONSIBLE_ID")
    responsible = ObjectBitrixField("responsibleId", object_type=USER_OBJECT, is_required=True, field_code_to_bitrix="RESPONSIBLE_ID")
    changed_by = ObjectBitrixField("changedBy", object_type=USER_OBJECT, is_required=True, field_code_to_bitrix="CHANGED_BY")
    changed_date = DateTimeBitrixField("changedDate", is_required=True, field_code_to_bitrix="CHANGED_DATE")
    status_changed_by = ObjectBitrixField("statusChangedBy", object_type=USER_OBJECT, is_required=True, field_code_to_bitrix="STATUS_CHANGED_BY")
    status_changed_date = DateTimeBitrixField("statusChangedDate", is_required=True, field_code_to_bitrix="STATUS_CHANGED_DATE")
    closed_by = ObjectBitrixField("closedBy", object_type=USER_OBJECT, is_required=True, field_code_to_bitrix="CLOSED_BY")
    closed_date = DateTimeBitrixField("closedDate", field_code_to_bitrix="CLOSED_DATE")
    activity_date = DateTimeBitrixField("activityDate", field_code_to_bitrix="ACTIVITY_DATE")
    date_start = DateTimeBitrixField("dateStart", field_code_to_bitrix="DATE_START")
    deadline = DateTimeBitrixField("deadline", field_code_to_bitrix="DEADLINE")
    start_date_plan = DateTimeBitrixField("startDatePlan", field_code_to_bitrix="START_DATE_PLAN")
    end_date_plan = DateTimeBitrixField("endDatePlan", field_code_to_bitrix="END_DATE_PLAN")
    guid = TextBitrixField("guid", field_code_to_bitrix="GUID")
    xml_id = TextBitrixField("xmlId", field_code_to_bitrix="XML_ID")
    comments_count = IntBitrixField("commentsCount", is_required=True, field_code_to_bitrix="COMMENTS_COUNT")
    service_comments_count = IntBitrixField("serviceCommentsCount", is_required=True, field_code_to_bitrix="SERVICE_COMMENTS_COUNT")
    new_comments_count = IntBitrixField("newCommentsCount", is_required=True, field_code_to_bitrix="NEW_COMMENTS_COUNT")
    allow_change_deadline = BoolBitrixField("allowChangeDeadline", is_required=True, field_code_to_bitrix="ALLOW_CHANGE_DEADLINE")
    allow_time_tracking = BoolBitrixField("allowTimeTracking", is_required=True, field_code_to_bitrix="ALLOW_TIME_TRACKING")
    task_control = BoolBitrixField("taskControl", is_required=True, field_code_to_bitrix="TASK_CONTROL")
    add_in_report = BoolBitrixField("addInReport", is_required=True, field_code_to_bitrix="ADD_IN_REPORT")
    forked_by_template_id = BoolBitrixField("forkedByTemplateId", is_required=True, field_code_to_bitrix="FORKED_BY_TEMPLATE_ID")
    time_estimate = IntBitrixField("timeEstimate", is_required=True, field_code_to_bitrix="TIME_ESTIMATE")
    time_spent_in_logs = IntBitrixField("timeSpentInLogs", is_required=True, field_code_to_bitrix="TIME_SPENT_IN_LOGS")
    match_work_time = BoolBitrixField("matchWorkTime", is_required=True, field_code_to_bitrix="MATCH_WORK_TIME")
    forum_topic_id = IntBitrixField("forumTopicId", is_required=True, field_code_to_bitrix="FORUM_TOPIC_ID")
    forum_id = IntBitrixField("forumId", is_required=True, field_code_to_bitrix="FORUM_ID")
    site_id = TextBitrixField("siteId", is_required=True, field_code_to_bitrix="SITE_ID")
    subordinate = BoolBitrixField("subordinate", is_required=True, field_code_to_bitrix="SUBORDINATE")
    favorite = BoolBitrixField("favorite", is_required=True, field_code_to_bitrix="FAVORITE")
    exchange_modified = DateTimeBitrixField("exchangeModified", field_code_to_bitrix="EXCHANGE_MODIFIED")
    exchange_id = IntBitrixField("exchangeId", field_code_to_bitrix="EXCHANGE_ID")
    outlook_version = IntBitrixField("outlookVersion", field_code_to_bitrix="OUTLOOK_VERSION")
    viewed_date = DateTimeBitrixField("viewedDate", field_code_to_bitrix="VIEWED_DATE")
    sorting = FloatBitrixField("sorting", field_code_to_bitrix="SORTING")
    is_muted = BoolBitrixField("isMuted", is_required=True, field_code_to_bitrix="IS_MUTED")
    is_pinned = BoolBitrixField("isPinned", is_required=True, field_code_to_bitrix="IS_PINNED")
    is_pinned_in_group = BoolBitrixField("isPinnedInGroup", is_required=True, field_code_to_bitrix="IS_PINNED_IN_GROUP")
    flow_id = IntBitrixField("flowId", field_code_to_bitrix="FLOW_ID")
    description_in_bbcode = BoolBitrixField("descriptionInBbcode", is_required=True, field_code_to_bitrix="DESCRIPTION_IN_BBCODE")
    duration_plan = IntBitrixField("durationPlan", is_required=True, field_code_to_bitrix="DURATION_PLAN")
    duration_type = TextBitrixField("descriptionType", field_code_to_bitrix="DURATION_TYPE")
    duration_fact = IntBitrixField("durationFact", is_required=True, field_code_to_bitrix="DURATION_FACT")
    check_list_can_add = BoolBitrixField("checkListCanAdd", field_code_to_bitrix="CHECKLIST_CAN_ADD")
    auditors = ObjectBitrixField("auditors", object_type=USER_OBJECT, is_multiple=True, field_code_to_bitrix="AUDITORS")
    accomplices = ObjectBitrixField("accomplices", object_type=USER_OBJECT, is_multiple=True, field_code_to_bitrix="ACCOMPLICES")
    uf_crm_task = TextBitrixField("ufCrmTask", field_code_to_bitrix="UF_CRM_TASK", is_multiple=True)

    def __str__(self):
        return self.title.value

    def _get_bitrix_data(self) -> Dict:
        result = self.but.call_api_method("tasks.task.get", {"taskId": self.bitrix_id})["result"]
        return self._validate_api_get(result)

    def update(self, fields: Dict):
        """Обновить элемент"""
        self.but.call_api_method("tasks.task.update", {"taskId": self.bitrix_id, "fields": fields})

    def delete(self):
        """Удалить элемент"""
        self.but.call_api_method("tasks.task.delete", {"taskId": self.bitrix_id})

    def approve(self):
        """Принять задачу"""
        self.but.call_api_method("tasks.task.approve", {"taskId": self.bitrix_id})

    def complete(self):
        """Завершить задачу"""
        self.but.call_api_method("tasks.task.complete", {"taskId": self.bitrix_id})

    def defer(self):
        """Отложить задачу"""
        self.but.call_api_method("tasks.task.defer", {"taskId": self.bitrix_id})

    def delegate(self, user_id: int):
        """Делегировать задачу"""
        self.but.call_api_method("tasks.task.delegate", {"taskId": self.bitrix_id, "userId": user_id})

    def disapprove(self):
        """Отклонить задачу"""
        self.but.call_api_method("tasks.task.disapprove", {"taskId": self.bitrix_id})

    def add_favorite(self):
        """Додавить задачу в Избранное"""
        self.but.call_api_method("tasks.task.favorite.add", {"taskId": self.bitrix_id})

    def remove_favorite(self):
        """Удалить задачу из Избранного"""
        self.but.call_api_method("tasks.task.favorite.remove", {"taskId": self.bitrix_id})

    def attach_files(self, file_id: int):
        """Прикрепление загруженного на диск файла к задаче"""
        self.but.call_api_method("tasks.task.files.attach", {"taskId": self.bitrix_id, "fileId": file_id})

    def get_access(self, user_ids: Iterable[int] = tuple()) -> Dict["USER_OBJECT", Dict[Text, bool]]:
        """Проверка доступо к задаче для переданных пользователей. По умолчанию берется текущий пользователь.
        Возвращает словарь вида: {user_object: {Действие: доступ}}"""
        user_class = self.get_class(self.USER_OBJECT)
        user_actions = self.but.call_list_method("tasks.task.getaccess", {"taskId": self.bitrix_id, "users": list(user_ids) or [self.but.user.bitrix_id]})["allowedActions"]
        return {user_class(user_id, but=self.but): actions for user_id, actions in user_actions.items()}

    def mute(self):
        """Включить режим 'Без звука'"""
        self.but.call_api_method("tasks.task.mute", {"id": self.bitrix_id})

    def unmute(self):
        """Выключить режим 'Без звука'"""
        self.but.call_api_method("tasks.task.unmute", {"id": self.bitrix_id})

    def pause(self):
        """Переводит задачу в статус 'Ждет выполнения'"""
        self.but.call_api_method("tasks.task.pause", {"taskId": self.bitrix_id})

    def start(self):
        """Переводит задачу в статус 'Выполняется'"""
        self.but.call_api_method("tasks.task.start", {"taskId": self.bitrix_id})

    def renew(self):
        """Возобновить задачу"""
        self.but.call_api_method("tasks.task.renew", {"taskId": self.bitrix_id})

    def start_watch(self):
        """Начать наблюдать за задачей"""
        self.but.call_api_method("tasks.task.startwatch", {"taskId": self.bitrix_id})

    def stop_watch(self):
        """Перестать наблюдать за задачей"""
        self.but.call_api_method("tasks.task.stopwatch", {"taskId": self.bitrix_id})

    def start_timer(self):
        """Начать учет времени по задаче"""
        self.but.call_api_method("tasks.task.startTimer", {"taskId": self.bitrix_id})

    def pause_timer(self):
        """Остановить учет времени по задаче"""
        self.but.call_api_method("tasks.task.pauseTimer", {"taskId": self.bitrix_id})

    def add_accomplices(self, user_ids: Iterable[int]):
        """Добавить соисполнителей"""
        self.accomplices.value = list(set(self.accomplices.value).union(user_ids))
        self.save(update_fields=["accomplices"])

    def add_auditors(self, user_ids: Iterable[int]):
        """Добавить наблюдателей"""
        self.auditors.value = list(set(self.auditors.value).union(user_ids))
        self.save(update_fields=["auditors"])

    @staticmethod
    def _validate_api_get(api_data: Dict) -> Dict:
        if isinstance(api_data, dict):
            return api_data["task"]
        else:
            raise NotFoundObject("Задача не найдена на портале")

    @property
    def url(self) -> Text:
        """Ссылка на задачу"""
        return f"{self.portal_url}/company/personal/user/{self.created_by.value}/tasks/task/view/{self.bitrix_id}/"
