import unittest

from example import dispatch_tool, local_adapter


class ToolDispatchTests(unittest.TestCase):

    def test_add(self):
        self.assertEqual(
            dispatch_tool("add", {"a": 2, "b": 3}),
            {"ok": True, "result": 5}
        )

    def test_multiply(self):
        self.assertEqual(
            dispatch_tool("multiply", {"a": 2, "b": 3}),
            {"ok": True, "result": 6}
        )

    def test_unknown_tool(self):
        result = dispatch_tool("divide", {"a": 2, "b": 3})
        self.assertFalse(result["ok"])
        self.assertEqual(
            result["error"]["type"], "invalid_tool_call"
        )

    def test_string_argument(self):
        result = dispatch_tool("add", {"a": "2", "b": 3})
        self.assertFalse(result["ok"])

    def test_boolean_argument(self):
        result = dispatch_tool("add", {"a": True, "b": 3})
        self.assertFalse(result["ok"])

    def test_missing_argument(self):
        result = dispatch_tool("add", {"a": 2})
        self.assertFalse(result["ok"])

    def test_failed_call_does_not_execute_another_tool(self):
        calls = []

        def tracking_adapter(tool_name, arguments):
            calls.append(tool_name)
            return local_adapter(tool_name, arguments)

        result = dispatch_tool(
            "unknown",
            {"a": 2, "b": 3},
            adapter=tracking_adapter
        )

        self.assertFalse(result["ok"])
        self.assertEqual(calls, ["unknown"])


if __name__ == "__main__":
    unittest.main()