from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Protocol

from ..server import McpTool, McpToolResult


class ActionError(ValueError):
    """A safe, structured error a project adapter may return to an MCP client."""

    def __init__(self, error: str, **details: Any) -> None:
        self.error = error
        self.details = details
        super().__init__(error)

    def to_payload(self) -> dict[str, Any]:
        return {"error": self.error, **self.details}


class TaskOperation(StrEnum):
    GET_BY_ID = "get_by_id"
    SEARCH_BY_DESCRIPTION = "search_by_description"
    SEARCH_BY_COMMENTS = "search_by_comments"
    SEARCH_BY_FULL = "search_by_full"

    @property
    def description(self) -> str:
        return {
            self.GET_BY_ID: "Get task by id",
            self.SEARCH_BY_DESCRIPTION: "Search tasks by description",
            self.SEARCH_BY_COMMENTS: "Search tasks by comments",
            self.SEARCH_BY_FULL: "Search tasks by full text",
        }[self]


@dataclass(frozen=True, slots=True)
class TaskReaderParams:
    operation: TaskOperation
    task_id: int | None = None
    query: str | None = None
    limit: int | None = None


class TaskSource(Protocol):
    """Project adapter for one task data source, such as B24 DB or Bitrix REST."""

    name: str
    supported_operations: frozenset[TaskOperation]

    def execute(self, params: TaskReaderParams) -> dict[str, Any]:
        """Return the normalized task-reader payload or raise ``ActionError``."""


class TaskReaderAction:
    """Reusable MCP action that delegates task reads to a project-selected source."""

    def __init__(self, source: TaskSource, *, tool_name: str = "b24_task_read") -> None:
        self.source = source
        self.tool_name = tool_name

    def as_tool(self) -> McpTool:
        return McpTool(self.tool_name, self.schema(), self.execute)

    def schema(self) -> dict[str, Any]:
        operations = [operation.value for operation in self.supported_operations]
        return {
            "name": self.tool_name,
            "title": "Read Bitrix24 task",
            "description": (
                "Read-only access to Bitrix24 tasks from the configured source. "
                "Use operation=get_by_id with task_id, or a supported search operation "
                "with q and optional limit. "
                f"Available operations: {operations}."
            ),
            "inputSchema": {
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "enum": operations,
                        "description": "Task reader operation",
                    },
                    "task_id": {
                        "type": "integer",
                        "minimum": 1,
                        "description": "Required for get_by_id",
                    },
                    "q": {
                        "type": "string",
                        "minLength": 1,
                        "description": "Required for search operations",
                    },
                    "limit": {
                        "type": "integer",
                        "minimum": 1,
                        "description": "Optional max results for search operations",
                    },
                },
                "required": ["operation"],
                "additionalProperties": False,
            },
            "annotations": {
                "title": "Read Bitrix24 task",
                "readOnlyHint": True,
                "destructiveHint": False,
                "idempotentHint": True,
                "openWorldHint": False,
            },
        }

    @property
    def supported_operations(self) -> tuple[TaskOperation, ...]:
        return tuple(operation for operation in TaskOperation if operation in self.source.supported_operations)

    def execute(self, arguments: Mapping[str, Any]) -> McpToolResult:
        try:
            params = self.parse_arguments(arguments)
            return McpToolResult(self.source.execute(params))
        except ActionError as exc:
            return McpToolResult(exc.to_payload(), is_error=True)

    def parse_arguments(self, arguments: Mapping[str, Any]) -> TaskReaderParams:
        operation_value = arguments.get("operation")
        try:
            operation = TaskOperation(operation_value)
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

        if operation is TaskOperation.GET_BY_ID:
            task_id = self.parse_positive_int(arguments.get("task_id"), "task_id", required=True)
            return TaskReaderParams(operation=operation, task_id=task_id)

        query = arguments.get("q")
        if not isinstance(query, str) or not query.strip():
            raise ActionError("missing_query", param="q")
        limit = self.parse_positive_int(arguments.get("limit"), "limit", required=False)
        return TaskReaderParams(operation=operation, query=query.strip(), limit=limit)

    @staticmethod
    def parse_positive_int(value: Any, param: str, *, required: bool) -> int | None:
        if value is None:
            if required:
                raise ActionError(f"missing_{param}", param=param)
            return None
        if isinstance(value, bool) or not isinstance(value, int) or value < 1:
            raise ActionError(f"invalid_{param}", param=param)
        return value
