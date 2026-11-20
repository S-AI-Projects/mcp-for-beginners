import unittest

from example import ToolDispatcher


class TestToolDispatcher(unittest.TestCase):

    def setUp(self):
        self.dispatcher = ToolDispatcher()

    def test_add(self):
        response = self.dispatcher.dispatch_json(
            '{"tool": "add", "arguments": {"a": 2, "b": 3}}'
        )
        self.assertTrue(response["ok"])
        self.assertEqual(response["result"], 5)

    def test_multiply(self):
        response = self.dispatcher.dispatch_json(
            '{"tool": "multiply", "arguments": {"a": 2, "b": 3}}'
        )
        self.assertTrue(response["ok"])
        self.assertEqual(response["result"], 6)

    def test_boundary_values(self):
        response = self.dispatcher.dispatch_json(
            '{"tool": "add", "arguments": {"a": 0, "b": -5}}'
        )
        self.assertTrue(response["ok"])
        self.assertEqual(response["result"], -5)

    def test_unknown_tool(self):
        response = self.dispatcher.dispatch_json(
            '{"tool": "divide", "arguments": {"a": 8, "b": 2}}'
        )
        self.assertFalse(response["ok"])
        self.assertEqual(response["error"]["code"], "UNKNOWN_TOOL")
        self.assertNotIn("tool_executed", response["trace"])
        self.assertEqual(self.dispatcher.execution_log, [])

    def test_invalid_string_argument(self):
        response = self.dispatcher.dispatch_json(
            '{"tool": "add", "arguments": {"a": "2", "b": 3}}'
        )
        self.assertFalse(response["ok"])
        self.assertEqual(response["error"]["code"], "INVALID_ARGUMENTS")
        self.assertNotIn("tool_executed", response["trace"])
        self.assertEqual(self.dispatcher.execution_log, [])

    def test_invalid_json(self):
        response = self.dispatcher.dispatch_json("{invalid json")
        self.assertFalse(response["ok"])
        self.assertEqual(response["error"]["code"], "INVALID_JSON")

    def test_missing_argument(self):
        response = self.dispatcher.dispatch_json(
            '{"tool": "add", "arguments": {"a": 2}}'
        )
        self.assertFalse(response["ok"])
        self.assertEqual(response["error"]["code"], "INVALID_ARGUMENTS")

    def test_trace_invariant(self):
        response = self.dispatcher.dispatch_json(
            '{"tool": "add", "arguments": {"a": 2, "b": 3}}'
        )
        trace = response["trace"]

        self.assertTrue(response["ok"])
        self.assertIn("arguments_validated", trace)
        self.assertIn("tool_executed", trace)
        self.assertIn("result_recorded", trace)
        self.assertEqual(response["result"], 5)
        self.assertLess(
            trace.index("arguments_validated"),
            trace.index("tool_executed")
        )
        self.assertLess(
            trace.index("tool_executed"),
            trace.index("result_recorded")
        )

if __name__ == "__main__":
    unittest.main()