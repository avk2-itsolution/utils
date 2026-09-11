from __future__ import annotations

import traceback
from collections.abc import Callable
from typing import Any

from rest_framework import status
from rest_framework.exceptions import ParseError
from rest_framework.parsers import JSONParser
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from ..config import McpConfigurationError
from ..server import McpServer, McpToolResult
from .authentication import McpBearerAuthentication
from .permissions import McpOriginPermission


ServerBuilder = Callable[[], McpServer]


class McpServerBoundView(APIView):
    server_builder: ServerBuilder | None = None

    def build_server(self) -> McpServer:
        if self.server_builder is None:
            raise RuntimeError("MCP server builder was not configured")
        return self.server_builder()

    @staticmethod
    def log_exception(error_place: str, exc: Exception) -> None:
        import logging
        logging.getLogger("assistant_mcp").error("%s: %s\n%s", error_place, exc, traceback.format_exc())


class McpHttpView(McpServerBoundView):
    http_method_names = ["get", "post"]
    authentication_classes = [McpBearerAuthentication]
    permission_classes = [McpOriginPermission]
    parser_classes = [JSONParser]

    def post(self, request: Request) -> Response:
        server = self.build_server()
        try:
            message = request.data
        except ParseError:
            return Response(server.error_response(None, -32700, "Parse error"), status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:
            self.log_exception("assistant_mcp.django.mcp_post_parse", exc)
            return Response(server.error_response(None, -32603, "Internal error"), status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        if self.is_json_rpc_response(message):
            return Response(status=status.HTTP_202_ACCEPTED)
        try:
            response = server.handle_message(message)
        except Exception as exc:
            self.log_exception("assistant_mcp.django.mcp_handle_message", exc)
            return Response(server.error_response(None, -32603, "Internal error"), status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(status=status.HTTP_202_ACCEPTED) if response is None else Response(response)

    def get(self, request: Request) -> Response:
        return Response({"error": "sse_not_supported"}, status=status.HTTP_405_METHOD_NOT_ALLOWED, headers={"Allow": "POST"})

    @staticmethod
    def is_json_rpc_response(message: Any) -> bool:
        return isinstance(message, dict) and "method" not in message and ("result" in message or "error" in message)


class ToolRestView(McpServerBoundView):
    tool_name = ""
    authentication_classes: list[type] = []
    permission_classes: list[type] = []
    http_method_names = ["get"]

    def get(self, request: Request, operation: str) -> Response:
        try:
            result = self.execute_tool(self.build_server(), self.arguments_from_request(request, operation))
            return Response(result.value, status=self.error_status(result))
        except McpConfigurationError as exc:
            return Response({"error": "configuration_error", "detail": str(exc)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except Exception as exc:
            self.log_exception(f"assistant_mcp.django.{self.tool_name}", exc)
            return Response({"error": "internal_error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @staticmethod
    def arguments_from_request(request: Request, operation: str) -> dict[str, Any]:
        arguments: dict[str, Any] = {**request.query_params.dict(), "operation": operation}
        for key in {"task_id", "template_id", "auto_execute", "started_by", "user_id", "status", "limit"}:
            value = arguments.get(key)
            if isinstance(value, str):
                try:
                    arguments[key] = int(value)
                except ValueError:
                    pass
        return arguments

    def execute_tool(self, server: McpServer, arguments: dict[str, Any]) -> McpToolResult:
        tool = server.tools.get(self.tool_name)
        if tool is None:
            return McpToolResult({"error": f"{self.tool_name}_disabled"}, is_error=True)
        result = tool.handler(arguments)
        return result if isinstance(result, McpToolResult) else McpToolResult(result)

    @staticmethod
    def error_status(result: McpToolResult) -> int:
        if not result.is_error:
            return status.HTTP_200_OK
        error = result.value.get("error")
        if error in {"task_not_found", "template_not_found", "instance_not_found"}:
            return status.HTTP_404_NOT_FOUND
        if error == "template_actions_not_available":
            return status.HTTP_422_UNPROCESSABLE_ENTITY
        if error == "bitrix_rest_error":
            return status.HTTP_502_BAD_GATEWAY
        if error in {"missing_group_id", "invalid_group_id", "configuration_error"}:
            return status.HTTP_503_SERVICE_UNAVAILABLE
        if error in {"operation_not_supported", "operation_not_implemented"}:
            return status.HTTP_501_NOT_IMPLEMENTED
        if error == "internal_error":
            return status.HTTP_500_INTERNAL_SERVER_ERROR
        return status.HTTP_400_BAD_REQUEST


class TaskReaderView(ToolRestView):
    tool_name = "b24_task_read"


class BusinessProcessReaderView(ToolRestView):
    tool_name = "b24_bizproc_read"
    authentication_classes = [McpBearerAuthentication]
    permission_classes = [McpOriginPermission]


class ManifestView(McpServerBoundView):
    http_method_names = ["get"]

    def get(self, request: Request) -> Response:
        server = self.build_server()
        return Response({"name": "assistant_mcp", "read_only": True, "resources": [tool.schema for tool in server.tools.values()]})


class ToolManifestView(McpServerBoundView):
    tool_name = ""
    http_method_names = ["get"]

    def get(self, request: Request) -> Response:
        tool = self.build_server().tools.get(self.tool_name)
        if tool is None:
            return Response({"error": f"{self.tool_name}_disabled"}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        return Response({"name": tool.name, "read_only": True, "input_schema": tool.schema.get("inputSchema", {})})
