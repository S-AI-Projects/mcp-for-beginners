
import unittest
import json

from example import LocalServiceAdapter, ToolDispatcher


class TestToolDispatcher(unittest.TestCase):

    def setUp(self):
        self.service = LocalServiceAdapter()
        self.dispatcher = ToolDispatcher(self.service)

    def call_tool(self, tool, arguments):
        request = json.dumps({
            "tool": tool,
            "arguments": arguments
        })
        return self.dispatcher.dispatch(request)

    def test_add(self):
        result = self.call_tool("add", {"a": 2, "b": 3})
        self.assertEqual(result["result"], 5)

    def test_multiply(self):
        result = self.call_tool("multiply", {"a": 2, "b": 3})
        self.assertEqual(result["result"], 6)

    def test_unknown_tool(self):
        result = self.call_tool("divide", {"a": 2, "b": 3})
        self.assertEqual(result["error"]["code"], "UNKNOWN_TOOL")

    def test_string_argument(self):
        result = self.call_tool("add", {"a": "2", "b": 3})
        self.assertEqual(
            result["error"]["code"], "INVALID_ARGUMENT_TYPE"
        )

    def test_boolean_argument(self):
        result = self.call_tool("add", {"a": True, "b": 3})
        self.assertFalse(result["success"])

    def test_missing_argument(self):
        result = self.call_tool("add", {"a": 2})
        self.assertFalse(result["success"])

    def test_invalid_json(self):
        result = self.dispatcher.dispatch("{invalid json")
        self.assertEqual(result["error"]["code"], "INVALID_JSON")

    def test_failed_call_does_not_execute_another_tool(self):
        self.call_tool("divide", {"a": 2, "b": 3})
        self.assertEqual(self.service.execution_log, [])

    def test_valid_call_executes_once(self):
        self.call_tool("add", {"a": 2, "b": 3})
        self.assertEqual(self.service.execution_log, ["add"])


if __name__ == "__main__":
    unittest.main()
