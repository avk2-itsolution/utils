"""Reusable MCP transport primitives for project-specific assistant tools."""

from .server import McpServer, McpTool, McpToolResult, ServerInfo
from .registry import DuplicateToolNameError, ToolRegistry
from .app import McpLocalExtensions, build_mcp_server
from .config import McpConfigurationError, ProjectMcpConfig

__all__ = [
    "DuplicateToolNameError",
    "McpServer",
    "McpConfigurationError",
    "McpLocalExtensions",
    "McpTool",
    "McpToolResult",
    "ServerInfo",
    "ToolRegistry",
    "ProjectMcpConfig",
    "build_mcp_server",
]
