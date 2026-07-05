from utils.bitrix_utils.bitrix_objects.crm.base_activity_object.base_activity_object_manager import BaseActivityObjectManager
from utils.bitrix_utils.bitrix_objects.crm.crm_object import CRMObject
from utils.bitrix_utils.bitrix_objects.main.fields import (
    TextBitrixField,
    IntBitrixField,
    FloatBitrixField,
    DateTimeBitrixField,
    BoolBitrixField,
    DictBitrixField,
    ObjectBitrixField,
)


class BaseActivityObject(CRMObject):
    """Дело CRM (activity) — готовый класс для чтения/создания.

    Examples:
        >>> act = BaseActivityObject.objects(but).get(bitrix_id=9001)
        >>> act.subject.value
    """

    ENTITY_TYPE_NAME = "ACTIVITY"
    USER_FIELD_ENTITY_ID = "CRM_ACTIVITY"

    USER_OBJECT = "utils.bitrix_utils.bitrix_objects.users.BaseUserObject"

    _objects = BaseActivityObjectManager

    owner_id = IntBitrixField("OWNER_ID", is_required=True)
    owner_type_id = IntBitrixField("OWNER_TYPE_ID", is_required=True)
    # 1 — CALL, 2 — EMAIL, 3 — TASK, 4 — MEETING, 5 — INCOMING, 6 — OUTGOING, 7 — OTHER
    type_id = IntBitrixField("TYPE_ID", is_required=True)
    provider_id = TextBitrixField("PROVIDER_ID", is_required=True)
    provider_type_id = TextBitrixField("PROVIDER_TYPE_ID", is_required=True)
    provider_group_id = TextBitrixField("PROVIDER_GROUP_ID")
    associated_entity_id = IntBitrixField("ASSOCIATED_ENTITY_ID", is_required=True)
    subject = TextBitrixField("SUBJECT", is_required=True)
    start_time = DateTimeBitrixField("START_TIME")
    end_time = DateTimeBitrixField("END_TIME")
    deadline = DateTimeBitrixField("DEADLINE")
    completed = BoolBitrixField("COMPLETED", is_required=True)
    status = IntBitrixField("STATUS", is_required=True)
    responsible = ObjectBitrixField("RESPONSIBLE_id", object_type=USER_OBJECT)
    priority = IntBitrixField("PRIORITY", is_required=True)
    notify_type = IntBitrixField("NOTIFY_TYPE", is_required=True)
    notify_value = TextBitrixField("NOTIFY_VALUE", is_required=True)
    description = TextBitrixField("DESCRIPTION")
    description_type = IntBitrixField("DESCRIPTION_TYPE", is_required=True)
    direction = IntBitrixField("DIRECTION", is_required=True)
    location = TextBitrixField("LOCATION")
    created = DateTimeBitrixField("CREATED", is_required=True)
    author = ObjectBitrixField("AUTHOR_ID", object_type=USER_OBJECT)
    last_updated = DateTimeBitrixField("LAST_UPDATED", is_required=True)
    editor = ObjectBitrixField("EDITOR_ID", object_type=USER_OBJECT)
    settings = DictBitrixField("SETTINGS")
    origin_id = TextBitrixField("ORIGIN_ID")
    originator_id = TextBitrixField("ORIGINATOR_ID")
    origin_version = TextBitrixField("ORIGIN_VERSION")
    result_status = IntBitrixField("RESULT_STATUS")
    result_stream = IntBitrixField("RESULT_STREAM")
    result_source_id = TextBitrixField("RESULT_SOURCE_ID")
    result_mark = IntBitrixField("RESULT_MARK")
    provider_params = DictBitrixField("PROVIDER_PARAMS")
    provider_data = TextBitrixField("PROVIDER_DATA")
    result_value = FloatBitrixField("RESULT_VALUE")
    result_sum = FloatBitrixField("RESULT_SUM")
    result_currency_id = TextBitrixField("RESULT_CURRENCY_ID")
    autocomplete_rule = IntBitrixField("AUTOCOMPLETE_RULE")
    bindings = IntBitrixField("BINDINGS", is_multiple=True)
    communications = IntBitrixField("COMMUNICATIONS", is_multiple=True)
    files = DictBitrixField("FILES", is_multiple=True)
    webdav_elements = DictBitrixField("WEBDAV_ELEMENTS", is_multiple=True)
    is_incoming_channel = BoolBitrixField("IS_INCOMING_CHANNEL")
