from __future__ import annotations

import unittest

from utils.assistant_mcp import McpConfigurationError, McpLocalExtensions, build_mcp_server
from utils.assistant_mcp.actions import ActionError, BusinessProcessOperation, BusinessProcessReaderParams, TaskOperation, TaskReaderParams
from utils.assistant_mcp.bitrix import BitrixRestBusinessProcessSource, BitrixRestTaskSource
from utils.assistant_mcp.config import McpConfigurationError, ProjectMcpConfig


class FakeTransport:
    def __init__(self) -> None:
        self.calls = []

    def call_api_method(self, method, fields):
        self.calls.append((method, fields))
        return {"result": {"task": {"id": "7", "groupId": "12"}}}

    def call_list_method(self, method, *, fields, limit=None):
        self.calls.append((method, fields, limit))
        return [{"ID": str(index)} for index in range(50)]


class FakeTaskSource:
    name = "local_db"
    supported_operations = frozenset({TaskOperation.GET_BY_ID})

    def execute(self, params):
        return {"source": self.name, "task_id": params.task_id}


class ConfigAndBitrixTest(unittest.TestCase):
    def test_config_keeps_local_source_as_a_string_key(self):
        config = ProjectMcpConfig.from_mapping({"tools": {"task_reader": {"source": "b24_db", "group_id": 12}}})
        self.assertEqual(config.task_reader.source, "b24_db")
        self.assertEqual(config.task_reader.group_id, 12)

    def test_config_rejects_invalid_group_id(self):
        with self.assertRaises(McpConfigurationError):
            ProjectMcpConfig.from_mapping({"tools": {"task_reader": {"group_id": True}}})

    def test_business_process_limit_slices_the_first_bitrix_page(self):
        source = BitrixRestBusinessProcessSource(FakeTransport())
        result = source.execute(BusinessProcessReaderParams(BusinessProcessOperation.SEARCH_TEMPLATES, {"operation": "search_templates", "limit": 1}))
        self.assertEqual(result["returned_count"], 1)
        self.assertEqual(len(result["templates"]), 1)
        self.assertEqual(result["limit"], 1)

    def test_rest_task_source_uses_configured_group(self):
        source = BitrixRestTaskSource(FakeTransport(), group_id=12)
        result = source.execute(TaskReaderParams(TaskOperation.GET_BY_ID, task_id=7))
        self.assertEqual(result["source"], "bitrix_rest")

    def test_builder_uses_a_project_registered_local_source(self):
        config = ProjectMcpConfig.from_mapping({
            "tools": {
                "task_reader": {"source": "local_db"},
                "business_process_reader": {"enabled": False},
                "log_reader": {"enabled": False},
            }
        })
        server = build_mcp_server(config, McpLocalExtensions(task_sources={"local_db": FakeTaskSource()}))
        result = server.call_tool({"name": "b24_task_read", "arguments": {"operation": "get_by_id", "task_id": 3}})
        self.assertEqual(result["structuredContent"]["source"], "local_db")

    def test_builder_rejects_unknown_source_without_fallback(self):
        config = ProjectMcpConfig.from_mapping({
            "tools": {
                "task_reader": {"source": "missing"},
                "business_process_reader": {"enabled": False},
                "log_reader": {"enabled": False},
            }
        })
        with self.assertRaises(McpConfigurationError):
            build_mcp_server(config, McpLocalExtensions())
