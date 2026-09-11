from __future__ import annotations

import json
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from typing import Any


ToolHandler = Callable[[Mapping[str, Any]], "McpToolResult | Mapping[str, Any]"]


@dataclass(frozen=True, slots=True)
class ServerInfo:
    """Public identity reported during the MCP initialize handshake."""

    name: str
    title: str
    version: str


@dataclass(frozen=True, slots=True)
class McpToolResult:
    """A structured result of a tool call before it is serialized for MCP."""

    value: Mapping[str, Any]
    is_error: bool = False


@dataclass(frozen=True, slots=True)
class McpTool:
    """A project-registered MCP tool.

    The schema is the MCP tool descriptor returned by ``tools/list``. The
    handler stays independent of JSON-RPC and HTTP transport.
    """

    name: str
    schema: Mapping[str, Any]
    handler: ToolHandler

    def __post_init__(self) -> None:
        if self.schema.get("name") != self.name:
            raise ValueError("MCP tool schema name must match tool name")


class McpServer:
    """Reusable JSON-RPC MCP dispatcher with a project-provided tool registry."""

    supported_protocol_versions = ("2025-06-18", "2025-03-26", "2024-11-05")

    def __init__(self, *, info: ServerInfo, tools: Iterable[McpTool]):
        self.info = info
        self.tools: dict[str, McpTool] = {}
        for tool in tools:
            if tool.name in self.tools:
                raise ValueError(f"MCP tool is already registered: {tool.name}")
            self.tools[tool.name] = tool

    def handle_message(self, message: Any) -> dict[str, Any] | None:
        if not isinstance(message, dict):
            return self.error_response(None, -32600, "Invalid request")

        request_id = message.get("id")
        method = message.get("method")
        if not isinstance(method, str) or not method:
            return self.error_response(request_id, -32600, "Method is required")
        if method.startswith("notifications/"):
            return None

        match method:
            case "initialize":
                return self.result_response(
                    request_id,
                    self.initialize_result(message.get("params", {})),
                )
            case "ping":
                return self.result_response(request_id, {})
            case "tools/list":
                return self.result_response(
                    request_id,
                    {"tools": [tool.schema for tool in self.tools.values()]},
                )
            case "tools/call":
                return self.result_response(request_id, self.call_tool(message.get("params", {})))
            case "resources/list":
                return self.result_response(request_id, {"resources": []})
            case "prompts/list":
                return self.result_response(request_id, {"prompts": []})
            case _:
                return self.error_response(request_id, -32601, f"Method not found: {method}")

    def initialize_result(self, params: Any) -> dict[str, Any]:
        protocol_version = self.supported_protocol_versions[0]
        if isinstance(params, dict):
            requested_version = params.get("protocolVersion")
            if requested_version in self.supported_protocol_versions:
                protocol_version = requested_version

        return {
            "protocolVersion": protocol_version,
            "capabilities": {"tools": {"listChanged": False}},
            "serverInfo": {
                "name": self.info.name,
                "title": self.info.title,
                "version": self.info.version,
            },
        }

    def call_tool(self, params: Any) -> dict[str, Any]:
        if not isinstance(params, dict):
            return self.tool_result({"error": "invalid_params"}, is_error=True)

        arguments = params.get("arguments", {})
        if not isinstance(arguments, dict):
            return self.tool_result({"error": "invalid_arguments"}, is_error=True)

        tool = self.tools.get(params.get("name"))
        if tool is None:
            return self.tool_result(
                {"error": "tool_not_found", "tool": params.get("name")},
                is_error=True,
            )

        try:
            result = tool.handler(arguments)
        except Exception as exc:
            return self.tool_result(
                {"error": "internal_error", "detail": exc.__class__.__name__},
                is_error=True,
            )

        if isinstance(result, McpToolResult):
            return self.tool_result(result.value, is_error=result.is_error)
        return self.tool_result(result)

    @staticmethod
    def tool_result(value: Mapping[str, Any], *, is_error: bool = False) -> dict[str, Any]:
        result: dict[str, Any] = {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(value, ensure_ascii=False, indent=2),
                }
            ],
            "isError": is_error,
        }
        if not is_error:
            result["structuredContent"] = value
        return result

    @staticmethod
    def result_response(request_id: Any, result: Mapping[str, Any]) -> dict[str, Any]:
        return {"jsonrpc": "2.0", "id": request_id, "result": result}

    @staticmethod
    def error_response(
        request_id: Any,
        code: int,
        message: str,
        data: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        error: dict[str, Any] = {"code": code, "message": message}
        if data is not None:
            error["data"] = data
        return {"jsonrpc": "2.0", "id": request_id, "error": error}
