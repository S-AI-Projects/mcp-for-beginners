import unittest
from example import dispatch


class DispatchTests(unittest.TestCase):
    def setUp(self):
        self.log = []

    def test_add(self):
        result = dispatch(
            {"tool": "add", "arguments": {"a": 2, "b": 3}}, self.log
        )
        self.assertEqual(result, {"ok": True, "result": 5})

    def test_multiply(self):
        result = dispatch(
            {"tool": "multiply", "arguments": {"a": 2, "b": 3}}, self.log
        )
        self.assertEqual(result, {"ok": True, "result": 6})

    def test_unknown_tool_is_structured_error(self):
        result = dispatch(
            {"tool": "delete", "arguments": {"a": 2, "b": 3}}, self.log
        )
        self.assertFalse(result["ok"])
        self.assertEqual(result["error"]["code"], "UNKNOWN_TOOL")
        self.assertEqual(self.log, [])

    def test_string_argument_is_rejected(self):
        result = dispatch(
            {"tool": "add", "arguments": {"a": "2", "b": 3}}, self.log
        )
        self.assertFalse(result["ok"])
        self.assertEqual(result["error"]["code"], "INVALID_ARGUMENTS")
        self.assertEqual(self.log, [])

    def test_failed_call_does_not_execute_another_tool(self):
        dispatch(
            {"tool": "unknown", "arguments": {"a": 2, "b": 3}}, self.log
        )
        self.assertEqual(self.log, [])

    def test_valid_call_recovers_after_failure(self):
        failed = dispatch(
            {"tool": "add", "arguments": {"a": "2", "b": 3}}, self.log
        )
        recovered = dispatch(
            {"tool": "multiply", "arguments": {"a": 2, "b": 3}}, self.log
        )
        self.assertFalse(failed["ok"])
        self.assertEqual(recovered, {"ok": True, "result": 6})
        self.assertEqual(self.log, ["multiply"])

    def test_missing_arguments_are_rejected(self):
        result = dispatch({"tool": "add"}, self.log)
        self.assertEqual(result["error"]["code"], "INVALID_ARGUMENTS")


if __name__ == "__main__":
    unittest.main()
