from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Protocol

from ..server import McpTool, McpToolResult
from .task_reader import ActionError, reject_unknown_arguments


class BusinessProcessOperation(StrEnum):
    GET_TEMPLATE_BY_ID = "get_template_by_id"
    SEARCH_TEMPLATES = "search_templates"
    GET_TEMPLATE_ACTIONS = "get_template_actions"
    GET_INSTANCE_BY_ID = "get_instance_by_id"
    SEARCH_INSTANCES = "search_instances"
    SEARCH_WORKFLOW_TASKS = "search_workflow_tasks"

    @property
    def description(self) -> str:
        return {
            self.GET_TEMPLATE_BY_ID: "Get business process template by id",
            self.SEARCH_TEMPLATES: "Search business process templates",
            self.GET_TEMPLATE_ACTIONS: "Get business process template action tree",
            self.GET_INSTANCE_BY_ID: "Get business process instance by id",
            self.SEARCH_INSTANCES: "Search active business process instances",
            self.SEARCH_WORKFLOW_TASKS: "Search business process workflow tasks",
        }[self]


@dataclass(frozen=True, slots=True)
class BusinessProcessReaderParams:
    operation: BusinessProcessOperation
    arguments: Mapping[str, Any]


class BusinessProcessSource(Protocol):
    """Project adapter for a Bitrix business-process transport."""

    name: str
    supported_operations: frozenset[BusinessProcessOperation]

    def execute(self, params: BusinessProcessReaderParams) -> dict[str, Any]:
        """Return a normalized result or raise ``ActionError``."""


class BusinessProcessReaderAction:
    """Reusable schema and MCP dispatch for a project-provided BP source."""

    def __init__(
        self,
        source: BusinessProcessSource,
        *,
        tool_name: str = "b24_bizproc_read",
    ) -> None:
        self.source = source
        self.tool_name = tool_name

    def as_tool(self) -> McpTool:
        return McpTool(self.tool_name, self.schema(), self.execute)

    @property
    def supported_operations(self) -> tuple[BusinessProcessOperation, ...]:
        return tuple(
            operation
            for operation in BusinessProcessOperation
            if operation in self.source.supported_operations
        )

    def schema(self) -> dict[str, Any]:
        operations = [operation.value for operation in self.supported_operations]
        return {
            "name": self.tool_name,
            "title": "Read Bitrix24 business processes",
            "description": (
                "Read-only access to Bitrix24 business process templates, template "
                "actions, active instances and workflow tasks through the configured "
                f"source. Available operations: {operations}."
            ),
            "inputSchema": {
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "enum": operations,
                        "description": "Business process reader operation",
                    },
                    "template_id": {"type": "integer", "minimum": 1},
                    "instance_id": {"type": "string", "minLength": 1},
                    "task_id": {"type": "integer", "minimum": 1},
                    "workflow_id": {"type": "string", "minLength": 1},
                    "q": {"type": "string", "minLength": 1},
                    "module_id": {"type": "string", "minLength": 1},
                    "entity": {"type": "string", "minLength": 1},
                    "document_type": {"type": "string", "minLength": 1},
                    "document_id": {"type": "string", "minLength": 1},
                    "auto_execute": {"type": "integer", "enum": [0, 1, 2, 3]},
                    "started_by": {"type": "integer", "minimum": 0},
                    "user_id": {"type": "integer", "minimum": 0},
                    "status": {"type": "integer", "minimum": 0},
                    "limit": {"type": "integer", "minimum": 1, "maximum": 50},
                },
                "required": ["operation"],
                "additionalProperties": False,
            },
            "annotations": {
                "title": "Read Bitrix24 business processes",
                "readOnlyHint": True,
                "destructiveHint": False,
                "idempotentHint": True,
                "openWorldHint": False,
            },
        }

    def execute(self, arguments: Mapping[str, Any]) -> McpToolResult:
        try:
            params = self.parse_arguments(arguments)
            return McpToolResult(self.source.execute(params))
        except ActionError as exc:
            return McpToolResult(exc.to_payload(), is_error=True)

    def parse_arguments(
        self,
        arguments: Mapping[str, Any],
    ) -> BusinessProcessReaderParams:
        reject_unknown_arguments(
            arguments,
            {
                "operation", "template_id", "instance_id", "task_id", "workflow_id",
                "q", "module_id", "entity", "document_type", "document_id",
                "auto_execute", "started_by", "user_id", "status", "limit",
            },
        )
        operation_value = arguments.get("operation")
        try:
            operation = BusinessProcessOperation(operation_value)
        except ValueError:
            raise ActionError(
                "operation_not_found",
                operation=operation_value,
                available_operations=[
                    {"code": item.value, "description": item.description}
                    for item in self.supported_operations
                ],
            )

        if operation not in self.source.supported_operations:
            raise ActionError(
                "operation_not_supported",
                operation=operation.value,
                source=self.source.name,
            )
        return BusinessProcessReaderParams(operation=operation, arguments=arguments)
