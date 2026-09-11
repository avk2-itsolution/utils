from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from typing import Any

from .actions import BusinessProcessReaderAction, LogReaderAction, LogSource, TaskReaderAction, TaskSource
from .bitrix import BitrixRestBusinessProcessSource, BitrixRestTaskSource, BitrixTransport
from .config import McpConfigurationError, ProjectMcpConfig
from .registry import ToolRegistry
from .server import McpServer, McpTool, ServerInfo


@dataclass(slots=True)
class McpLocalExtensions:
    """Explicit project capabilities; no project module is imported by utils."""

    token_provider: Callable[[], BitrixTransport] | None = None
    task_sources: Mapping[str, TaskSource] = field(default_factory=dict)
    log_source: LogSource | None = None
    local_tools: tuple[McpTool, ...] = ()


def build_mcp_server(config: ProjectMcpConfig, extensions: McpLocalExtensions) -> McpServer:
    registry = ToolRegistry()
    if config.task_reader.enabled:
        source = extensions.task_sources.get(config.task_reader.source)
        if source is None and config.task_reader.source == "bitrix_rest":
            source = BitrixRestTaskSource(require_transport(extensions), config.task_reader.group_id)
        if source is None:
            raise McpConfigurationError(f"Task source is not available: {config.task_reader.source}")
        registry.add(TaskReaderAction(source).as_tool())
    if config.business_process_reader_enabled:
        registry.add(BusinessProcessReaderAction(BitrixRestBusinessProcessSource(require_transport(extensions))).as_tool())
    if config.log_reader_enabled:
        if extensions.log_source is None:
            raise McpConfigurationError("Log reader is enabled but no local LogSource was registered")
        registry.add(LogReaderAction(extensions.log_source).as_tool())
    registry.extend(extensions.local_tools)
    return McpServer(info=ServerInfo(config.name, config.title, config.version), tools=registry)


def require_transport(extensions: McpLocalExtensions) -> BitrixTransport:
    if extensions.token_provider is None:
        raise McpConfigurationError("Bitrix transport is required by the enabled MCP action")
    return extensions.token_provider()
