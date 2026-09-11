from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Protocol

from ..server import McpTool, McpToolResult
from .task_reader import ActionError


class LogSource(Protocol):
    """Project adapter for a read-only application log store."""

    name: str

    def execute(self, arguments: Mapping[str, Any]) -> dict[str, Any]:
        """Return a normalized log-reader result or raise ``ActionError``."""


class LogReaderAction:
    """Reusable MCP tool contract for project-provided log sources."""

    periods = ("today", "yesterday", "last_24_hours", "last_7_days", "last_30_days")

    def __init__(self, source: LogSource, *, tool_name: str = "django_log_read") -> None:
        self.source = source
        self.tool_name = tool_name

    def as_tool(self) -> McpTool:
        return McpTool(self.tool_name, self.schema(), self.execute)

    def schema(self) -> dict[str, Any]:
        return {
            "name": self.tool_name,
            "title": "Read Django application logs",
            "description": (
                "Search application logs from newest to oldest. Use period for common "
                "intervals, q for a distinctive error fragment and before_id to page. "
                "Start without traceback for broad searches, then request it for relevant logs."
            ),
            "inputSchema": {
                "type": "object",
                "properties": {
                    "log_id": {"type": "integer", "minimum": 1},
                    "q": {"type": "string", "minLength": 1},
                    "application": {"type": "string", "minLength": 1},
                    "levels": {
                        "type": "array",
                        "items": {"type": "string", "enum": ["error", "warning", "info"]},
                        "minItems": 1,
                        "uniqueItems": True,
                    },
                    "period": {"type": "string", "enum": list(self.periods)},
                    "date_from": {"type": "string"},
                    "date_to": {"type": "string"},
                    "before_id": {"type": "integer", "minimum": 1},
                    "limit": {"type": "integer", "minimum": 1, "maximum": 500, "default": 100},
                    "include_traceback": {"type": "boolean", "default": False},
                },
                "additionalProperties": False,
            },
            "annotations": {
                "title": "Read Django application logs",
                "readOnlyHint": True,
                "destructiveHint": False,
                "idempotentHint": True,
                "openWorldHint": False,
            },
        }

    def execute(self, arguments: Mapping[str, Any]) -> McpToolResult:
        try:
            return McpToolResult(self.source.execute(arguments))
        except ActionError as exc:
            return McpToolResult(exc.to_payload(), is_error=True)
