from __future__ import annotations

from collections.abc import Callable

from django.urls import path

from ..server import McpServer
from .views import BusinessProcessReaderView, ManifestView, McpHttpView, TaskReaderView, ToolManifestView


def build_urlpatterns(build_server: Callable[[], McpServer]):
    """Return the historical /mcp/ routes bound explicitly to one project."""
    return [
        path("", ManifestView.as_view(server_builder=build_server), name="manifest"),
        path("business-processes/", ToolManifestView.as_view(server_builder=build_server, tool_name="b24_bizproc_read"), name="business_process_reader_manifest"),
        path("business-processes/<str:operation>/", BusinessProcessReaderView.as_view(server_builder=build_server), name="business_process_reader"),
        path("tasks/", ToolManifestView.as_view(server_builder=build_server, tool_name="b24_task_read"), name="task_reader_manifest"),
        path("tasks/<str:operation>/", TaskReaderView.as_view(server_builder=build_server), name="task_reader"),
        path("b24-tasks/", McpHttpView.as_view(server_builder=build_server), name="b24_tasks_mcp"),
    ]
