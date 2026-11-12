import unittest

from example import dispatch


class DispatchTests(unittest.TestCase):
    def setUp(self):
        self.log = []

    def test_add(self):
        self.assertEqual(
            dispatch({"tool": "add", "arguments": {"a": 2, "b": 3}}, self.log),
            {"ok": True, "result": 5},
        )
        self.assertEqual(self.log, ["add"])

    def test_multiply(self):
        self.assertEqual(
            dispatch({"tool": "multiply", "arguments": {"a": 2, "b": 3}}, self.log),
            {"ok": True, "result": 6},
        )

    def test_zero_boundary_is_valid(self):
        self.assertEqual(
            dispatch({"tool": "add", "arguments": {"a": 0, "b": 0}}, self.log),
            {"ok": True, "result": 0},
        )

    def test_negative_boundary_is_valid(self):
        self.assertEqual(
            dispatch({"tool": "multiply", "arguments": {"a": -2, "b": 3}}, self.log),
            {"ok": True, "result": -6},
        )

    def test_float_arguments_are_valid(self):
        self.assertEqual(
            dispatch({"tool": "add", "arguments": {"a": 0.5, "b": 0.5}}, self.log),
            {"ok": True, "result": 1.0},
        )

    def test_unknown_tool_is_rejected_without_execution(self):
        result = dispatch(
            {"tool": "divide", "arguments": {"a": 2, "b": 1}}, self.log
        )
        self.assertEqual(result["error"]["code"], "UNKNOWN_TOOL")
        self.assertEqual(self.log, [])

    def test_string_argument_is_rejected_without_execution(self):
        result = dispatch(
            {"tool": "add", "arguments": {"a": "2", "b": 3}}, self.log
        )
        self.assertEqual(result["error"]["code"], "INVALID_ARGUMENTS")
        self.assertEqual(self.log, [])

    def test_boolean_is_not_accepted_as_a_number(self):
        result = dispatch(
            {"tool": "add", "arguments": {"a": True, "b": 3}}, self.log
        )
        self.assertEqual(result["error"]["code"], "INVALID_ARGUMENTS")
        self.assertEqual(self.log, [])

    def test_missing_argument_is_rejected(self):
        result = dispatch({"tool": "add", "arguments": {"a": 2}}, self.log)
        self.assertEqual(result["error"]["code"], "INVALID_ARGUMENTS")
        self.assertEqual(self.log, [])

    def test_valid_call_works_after_failed_call(self):
        dispatch({"tool": "divide", "arguments": {"a": 2, "b": 1}}, self.log)
        result = dispatch(
            {"tool": "add", "arguments": {"a": 2, "b": 3}}, self.log
        )
        self.assertEqual(result, {"ok": True, "result": 5})
        self.assertEqual(self.log, ["add"])


if __name__ == "__main__":
    unittest.main()
