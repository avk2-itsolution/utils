from __future__ import annotations

import unittest

from utils.assistant_mcp import McpServer, McpTool, ServerInfo, ToolRegistry
from utils.assistant_mcp.actions import (
    ActionError,
    BusinessProcessOperation,
    BusinessProcessReaderAction,
    LogReaderAction,
    TaskOperation,
    TaskReaderAction,
    TaskReaderParams,
)


class FakeTaskSource:
    name = "fake"
    supported_operations = frozenset({TaskOperation.GET_BY_ID})

    def execute(self, params: TaskReaderParams):
        return {"source": self.name, "task_id": params.task_id}


class FakeBusinessProcessSource:
    name = "fake_bitrix"
    supported_operations = frozenset({BusinessProcessOperation.GET_TEMPLATE_BY_ID})

    def execute(self, params):
        return {"source": self.name, "operation": params.operation.value}


class FakeLogSource:
    name = "fake_logs"

    def execute(self, arguments):
        if arguments.get("q") == "bad":
            raise ActionError("invalid_query", param="q")
        return {"source": self.name, "count": 0, "logs": []}


class ToolRegistryTest(unittest.TestCase):
    def test_rejects_duplicate_tool_name(self):
        registry = ToolRegistry()
        registry.add(McpTool("one", {"name": "one"}, lambda arguments: {}))

        with self.assertRaisesRegex(ValueError, "already registered"):
            registry.add(McpTool("one", {"name": "one"}, lambda arguments: {}))


class ActionContractTest(unittest.TestCase):
    def test_task_schema_only_advertises_source_capabilities(self):
        action = TaskReaderAction(FakeTaskSource())

        operations = action.schema()["inputSchema"]["properties"]["operation"]["enum"]
        self.assertEqual(operations, ["get_by_id"])

        unsupported = action.execute({"operation": "search_by_full", "q": "x"})
        self.assertTrue(unsupported.is_error)
        self.assertEqual(unsupported.value["error"], "operation_not_supported")

    def test_task_action_validates_and_delegates(self):
        result = TaskReaderAction(FakeTaskSource()).execute(
            {"operation": "get_by_id", "task_id": 7}
        )

        self.assertFalse(result.is_error)
        self.assertEqual(result.value, {"source": "fake", "task_id": 7})

    def test_business_process_schema_only_advertises_source_capabilities(self):
        action = BusinessProcessReaderAction(FakeBusinessProcessSource())

        operations = action.schema()["inputSchema"]["properties"]["operation"]["enum"]
        self.assertEqual(operations, ["get_template_by_id"])

    def test_log_action_returns_source_error_as_mcp_error(self):
        result = LogReaderAction(FakeLogSource()).execute({"q": "bad"})

        self.assertTrue(result.is_error)
        self.assertEqual(result.value, {"error": "invalid_query", "param": "q"})


class McpServerTest(unittest.TestCase):
    def setUp(self):
        self.server = McpServer(
            info=ServerInfo(name="test", title="Test", version="1.0"),
            tools=[TaskReaderAction(FakeTaskSource()).as_tool()],
        )

    def test_initialize_tools_list_and_tools_call(self):
        initialized = self.server.handle_message(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {"protocolVersion": "2025-03-26"},
            }
        )
        self.assertEqual(initialized["result"]["protocolVersion"], "2025-03-26")

        tools = self.server.handle_message(
            {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}
        )
        self.assertEqual(tools["result"]["tools"][0]["name"], "b24_task_read")

        called = self.server.handle_message(
            {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": "b24_task_read",
                    "arguments": {"operation": "get_by_id", "task_id": 7},
                },
            }
        )
        self.assertFalse(called["result"]["isError"])
        self.assertEqual(called["result"]["structuredContent"]["task_id"], 7)


if __name__ == "__main__":
    unittest.main()
