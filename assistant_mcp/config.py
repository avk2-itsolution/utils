from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any


class McpConfigurationError(ValueError):
    """A project MCP setting is missing or has an invalid shape."""


@dataclass(frozen=True, slots=True)
class TaskReaderConfiguration:
    enabled: bool
    source: str
    group_id: int | None


@dataclass(frozen=True, slots=True)
class ProjectMcpConfig:
    """Portable configuration parsed from the project's ``MCP_ACTIONS`` setting."""

    name: str
    title: str
    version: str
    portal_domain: str | None
    task_reader: TaskReaderConfiguration
    business_process_reader_enabled: bool
    log_reader_enabled: bool
    local_actions: Mapping[str, Mapping[str, Any]]

    @classmethod
    def from_settings(cls, django_settings: Any) -> "ProjectMcpConfig":
        return cls.from_mapping(getattr(django_settings, "MCP_ACTIONS", None))

    @classmethod
    def from_mapping(cls, raw: Any) -> "ProjectMcpConfig":
        if raw is None:
            raw = {}
        if not isinstance(raw, Mapping):
            raise McpConfigurationError("MCP_ACTIONS must be a mapping")

        server = cls.mapping(raw.get("server", {}), "MCP_ACTIONS.server")
        tools = cls.mapping(raw.get("tools", {}), "MCP_ACTIONS.tools")
        task = cls.mapping(tools.get("task_reader", {}), "MCP_ACTIONS.tools.task_reader")
        local_actions = cls.mapping(raw.get("local_actions", {}), "MCP_ACTIONS.local_actions")

        source = task.get("source", "bitrix_rest")
        if not isinstance(source, str) or not source.strip():
            raise McpConfigurationError("MCP_ACTIONS.tools.task_reader.source must be a non-empty string")
        group_id = task.get("group_id")
        if group_id is not None and (isinstance(group_id, bool) or not isinstance(group_id, int) or group_id < 1):
            raise McpConfigurationError("MCP_ACTIONS.tools.task_reader.group_id must be a positive integer")
        cls.validate_local_actions(local_actions)

        return cls(
            name=cls.string(server.get("name", "bitrix-readonly-mcp"), "server.name"),
            title=cls.string(server.get("title", "Bitrix24 read-only data"), "server.title"),
            version=cls.string(server.get("version", "1.0.0"), "server.version"),
            portal_domain=cls.optional_string(server.get("portal_domain"), "server.portal_domain"),
            task_reader=TaskReaderConfiguration(
                enabled=cls.boolean(task.get("enabled", True), "task_reader.enabled"),
                source=source.strip(),
                group_id=group_id,
            ),
            business_process_reader_enabled=cls.boolean(
                cls.mapping(tools.get("business_process_reader", {}), "MCP_ACTIONS.tools.business_process_reader").get("enabled", True),
                "business_process_reader.enabled",
            ),
            log_reader_enabled=cls.boolean(
                cls.mapping(tools.get("log_reader", {}), "MCP_ACTIONS.tools.log_reader").get("enabled", True),
                "log_reader.enabled",
            ),
            local_actions=local_actions,
        )

    @staticmethod
    def mapping(value: Any, path: str) -> Mapping[str, Any]:
        if not isinstance(value, Mapping):
            raise McpConfigurationError(f"{path} must be a mapping")
        return value

    @staticmethod
    def string(value: Any, path: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise McpConfigurationError(f"MCP_ACTIONS.{path} must be a non-empty string")
        return value.strip()

    @classmethod
    def optional_string(cls, value: Any, path: str) -> str | None:
        return None if value is None else cls.string(value, path)

    @staticmethod
    def boolean(value: Any, path: str) -> bool:
        if not isinstance(value, bool):
            raise McpConfigurationError(f"MCP_ACTIONS.{path} must be a boolean")
        return value

    @staticmethod
    def validate_local_actions(value: Mapping[str, Any]) -> None:
        for key, action_settings in value.items():
            if not isinstance(key, str) or not key.strip():
                raise McpConfigurationError("MCP_ACTIONS.local_actions keys must be non-empty strings")
            if not isinstance(action_settings, Mapping):
                raise McpConfigurationError(f"MCP_ACTIONS.local_actions.{key} must be a mapping")
