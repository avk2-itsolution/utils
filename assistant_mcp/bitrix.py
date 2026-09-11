from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Protocol

from .actions import ActionError, BusinessProcessOperation, BusinessProcessReaderParams, TaskOperation, TaskReaderParams


class BitrixTransport(Protocol):
    """Only the Bitrix REST operations used by the reusable read-only actions."""

    def call_api_method(self, method: str, fields: Mapping[str, Any]) -> Mapping[str, Any]: ...

    def call_list_method(self, method: str, *, fields: Mapping[str, Any], limit: int | None = None) -> list[dict[str, Any]]: ...


class BitrixRestTaskSource:
    name = "bitrix_rest"
    supported_operations = frozenset({TaskOperation.GET_BY_ID})
    task_select = (
        "id", "title", "description", "groupId", "status", "priority", "stageId", "parentId",
        "responsible", "creator", "createdDate", "changedDate", "activityDate", "deadline", "closedDate",
    )

    def __init__(self, transport: BitrixTransport, group_id: int | None = None) -> None:
        self.transport = transport
        self.group_id = group_id

    def execute(self, params: TaskReaderParams) -> dict[str, Any]:
        if params.operation is not TaskOperation.GET_BY_ID or params.task_id is None:
            raise ActionError("operation_not_supported", operation=params.operation.value, source=self.name)
        try:
            response = self.transport.call_api_method("tasks.task.get", {"taskId": params.task_id, "select": list(self.task_select)})
        except Exception as exc:
            raise bitrix_error(exc)
        task = self.extract_task(response)
        if task is None or not self.is_in_scope(task):
            raise ActionError("task_not_found", task_id=params.task_id)
        return {"source": self.name, "task": task, "custom_fields": {}, "members": [], "comments": []}

    @staticmethod
    def extract_task(response: Mapping[str, Any]) -> dict[str, Any] | None:
        result = response.get("result")
        if isinstance(result, Mapping):
            task = result.get("task", result)
            return dict(task) if isinstance(task, Mapping) else None
        return None

    def is_in_scope(self, task: Mapping[str, Any]) -> bool:
        if self.group_id is None:
            return True
        try:
            return int(task.get("groupId", task.get("GROUP_ID"))) == self.group_id
        except (TypeError, ValueError):
            return False


@dataclass(frozen=True, slots=True)
class BusinessProcessRequest:
    query: str | None = None
    limit: int | None = 20
    template_id: int | None = None
    instance_id: str | None = None
    task_id: int | None = None
    workflow_id: str | None = None
    module_id: str | None = None
    entity: str | None = None
    document_type: str | None = None
    document_id: str | None = None
    auto_execute: int | None = None
    started_by: int | None = None
    user_id: int | None = None
    status: int | None = None


class BitrixRestBusinessProcessSource:
    """Full common BP implementation; a project supplies only ``BitrixTransport``."""

    name = "bitrix_rest"
    supported_operations = frozenset(BusinessProcessOperation)
    template_fields = ("ID", "NAME", "DESCRIPTION", "MODULE_ID", "ENTITY", "DOCUMENT_TYPE", "AUTO_EXECUTE", "PARAMETERS", "VARIABLES", "CONSTANTS", "MODIFIED", "USER_ID", "SYSTEM_CODE")
    instance_fields = ("ID", "MODIFIED", "OWNED_UNTIL", "MODULE_ID", "ENTITY", "DOCUMENT_ID", "STARTED", "STARTED_BY", "TEMPLATE_ID")
    workflow_task_fields = ("ID", "WORKFLOW_ID", "DOCUMENT_NAME", "DESCRIPTION", "NAME", "MODIFIED", "WORKFLOW_STARTED", "WORKFLOW_STARTED_BY", "OVERDUE_DATE", "WORKFLOW_TEMPLATE_ID", "WORKFLOW_TEMPLATE_NAME", "WORKFLOW_STATE", "STATUS", "USER_ID", "USER_STATUS", "MODULE_ID", "ENTITY", "DOCUMENT_ID", "ACTIVITY", "ACTIVITY_NAME", "DOCUMENT_URL", "PARAMETERS")

    def __init__(self, transport: BitrixTransport) -> None:
        self.transport = transport

    def execute(self, params: BusinessProcessReaderParams) -> dict[str, Any]:
        request = self.parse_request(params.arguments, params.operation)
        try:
            match params.operation:
                case BusinessProcessOperation.GET_TEMPLATE_BY_ID:
                    template = self.get_template(request.template_id, False)
                    return {"source": self.name, "template": self.require(template, "template", request.template_id)}
                case BusinessProcessOperation.GET_TEMPLATE_ACTIONS:
                    template = self.require(self.get_template(request.template_id, True), "template", request.template_id)
                    if "TEMPLATE" not in template:
                        raise ActionError("template_actions_not_available", identifier=request.template_id)
                    return {"source": self.name, "template_id": request.template_id, "template_name": template.get("NAME"), "actions": template["TEMPLATE"]}
                case BusinessProcessOperation.SEARCH_TEMPLATES:
                    values = self.search_templates(request)
                    return self.list_result("templates", values, request.limit)
                case BusinessProcessOperation.GET_INSTANCE_BY_ID:
                    instance = self.get_instance(request.instance_id)
                    return {"source": self.name, "active_only": True, "instance": self.require(instance, "instance", request.instance_id)}
                case BusinessProcessOperation.SEARCH_INSTANCES:
                    values = self.search_instances(request)
                    return {**self.list_result("instances", values, request.limit), "active_only": True}
                case BusinessProcessOperation.SEARCH_WORKFLOW_TASKS:
                    values = self.search_workflow_tasks(request)
                    return self.list_result("workflow_tasks", values, request.limit)
        except ActionError:
            raise
        except Exception as exc:
            raise bitrix_error(exc)
        raise ActionError("operation_not_supported", operation=params.operation.value, source=self.name)

    @staticmethod
    def list_result(key: str, values: list[dict[str, Any]], limit: int | None) -> dict[str, Any]:
        return {"source": "bitrix_rest", key: values, "returned_count": len(values), "total": len(values), "limit": limit}

    @staticmethod
    def require(value: dict[str, Any] | None, entity: str, identifier: str | int | None) -> dict[str, Any]:
        if value is None:
            raise ActionError(f"{entity}_not_found", **{f"{entity}_id": identifier})
        return value

    def get_template(self, template_id: int | None, include_actions: bool) -> dict[str, Any] | None:
        assert template_id is not None
        values = self.search_templates(BusinessProcessRequest(template_id=template_id, limit=1), include_actions)
        return values[0] if values else None

    def search_templates(self, request: BusinessProcessRequest, include_actions: bool = False) -> list[dict[str, Any]]:
        select = self.template_fields + (("TEMPLATE",) if include_actions else ())
        return self.list_call("bizproc.workflow.template.list", select, {"ID": request.template_id, "%NAME": request.query, "AUTO_EXECUTE": request.auto_execute, "MODULE_ID": request.module_id, "ENTITY": request.entity, "DOCUMENT_TYPE": request.document_type}, request.limit)

    def get_instance(self, instance_id: str | None) -> dict[str, Any] | None:
        assert instance_id is not None
        values = self.search_instances(BusinessProcessRequest(instance_id=instance_id, limit=1))
        return values[0] if values else None

    def search_instances(self, request: BusinessProcessRequest) -> list[dict[str, Any]]:
        return self.list_call("bizproc.workflow.instances", self.instance_fields, {"ID": request.instance_id, "TEMPLATE_ID": request.template_id, "DOCUMENT_ID": request.document_id, "STARTED_BY": request.started_by}, request.limit)

    def search_workflow_tasks(self, request: BusinessProcessRequest) -> list[dict[str, Any]]:
        return self.list_call("bizproc.task.list", self.workflow_task_fields, {"%NAME": request.query, "ID": request.task_id, "WORKFLOW_ID": request.workflow_id, "WORKFLOW_TEMPLATE_ID": request.template_id, "DOCUMENT_ID": request.document_id, "USER_ID": request.user_id, "STATUS": request.status}, request.limit)

    def list_call(self, method: str, select: tuple[str, ...], filters: Mapping[str, Any], limit: int | None) -> list[dict[str, Any]]:
        values = self.transport.call_list_method(method, fields={"SELECT": select, "FILTER": {key: value for key, value in filters.items() if value is not None}, "ORDER": {"ID": "DESC"}, "start": 0}, limit=limit)
        return list(values[:limit]) if limit is not None else list(values)

    @classmethod
    def parse_request(cls, arguments: Mapping[str, Any], operation: BusinessProcessOperation) -> BusinessProcessRequest:
        def string(name: str, required: bool = False) -> str | None:
            value = arguments.get(name)
            if value is None:
                if required:
                    raise ActionError(f"missing_{name}", param=name)
                return None
            if not isinstance(value, str) or not value.strip():
                raise ActionError(f"invalid_{name}", param=name)
            return value.strip()
        def integer(name: str, minimum: int = 0, required: bool = False) -> int | None:
            value = arguments.get(name)
            if value is None:
                if required:
                    raise ActionError(f"missing_{name}", param=name)
                return None
            if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
                raise ActionError(f"invalid_{name}", param=name)
            return value
        limit = integer("limit", 1)
        if limit is not None and limit > 50:
            raise ActionError("invalid_limit", param="limit")
        if operation in {BusinessProcessOperation.GET_TEMPLATE_BY_ID, BusinessProcessOperation.GET_TEMPLATE_ACTIONS}:
            return BusinessProcessRequest(template_id=integer("template_id", 1, True), limit=1)
        if operation is BusinessProcessOperation.GET_INSTANCE_BY_ID:
            return BusinessProcessRequest(instance_id=string("instance_id", True), limit=1)
        auto_execute = integer("auto_execute", 0)
        if auto_execute is not None and auto_execute not in {0, 1, 2, 3}:
            raise ActionError("invalid_auto_execute", param="auto_execute")
        if operation is BusinessProcessOperation.SEARCH_TEMPLATES:
            return BusinessProcessRequest(query=string("q"), limit=limit, module_id=string("module_id"), entity=string("entity"), document_type=string("document_type"), auto_execute=auto_execute)
        if operation is BusinessProcessOperation.SEARCH_INSTANCES:
            return BusinessProcessRequest(limit=20 if limit is None else limit, template_id=integer("template_id", 1), document_id=string("document_id"), started_by=integer("started_by"))
        return BusinessProcessRequest(query=string("q"), limit=20 if limit is None else limit, task_id=integer("task_id", 1), workflow_id=string("workflow_id"), template_id=integer("template_id", 1), document_id=string("document_id"), user_id=integer("user_id"), status=integer("status"))


def bitrix_error(exc: Exception) -> ActionError:
    error = getattr(exc, "error", None)
    description = getattr(exc, "error_description", None)
    details = {key: value for key, value in {"bitrix_error": error, "description": description}.items() if value}
    return ActionError("bitrix_rest_error", **details)
