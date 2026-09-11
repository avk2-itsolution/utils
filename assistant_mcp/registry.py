from __future__ import annotations

from collections.abc import Iterable, Iterator

from .server import McpTool


class DuplicateToolNameError(ValueError):
    """Raised when a project registers two tools with the same MCP name."""


class ToolRegistry:
    """Explicit, deterministic registry for standard and project-local tools."""

    def __init__(self, tools: Iterable[McpTool] = ()) -> None:
        self._tools: dict[str, McpTool] = {}
        self.extend(tools)

    def add(self, tool: McpTool) -> None:
        if tool.name in self._tools:
            raise DuplicateToolNameError(f"MCP tool is already registered: {tool.name}")
        self._tools[tool.name] = tool

    def extend(self, tools: Iterable[McpTool]) -> None:
        for tool in tools:
            self.add(tool)

    def __iter__(self) -> Iterator[McpTool]:
        return iter(self._tools.values())

    def __len__(self) -> int:
        return len(self._tools)
