
import unittest
from unittest.mock import Mock, patch

from example import dispatch


class TestToolDispatch(unittest.TestCase):

    # Normal cases
    def test_add(self):
        self.assertEqual(
            dispatch({"tool": "add", "arguments": {"a": 2, "b": 3}}),
            {"ok": True, "result": 5}
        )

    def test_multiply(self):
        self.assertEqual(
            dispatch({"tool": "multiply", "arguments": {"a": 2, "b": 3}}),
            {"ok": True, "result": 6}
        )

    # Boundary cases
    def test_zero_arguments(self):
        self.assertEqual(
            dispatch({"tool": "add", "arguments": {"a": 0, "b": 0}}),
            {"ok": True, "result": 0}
        )

    def test_negative_arguments(self):
        self.assertEqual(
            dispatch({"tool": "multiply", "arguments": {"a": -2, "b": 3}}),
            {"ok": True, "result": -6}
        )

    # Invalid cases
    def test_unknown_tool(self):
        self.assertEqual(
            dispatch({"tool": "divide", "arguments": {"a": 2, "b": 3}}),
            {"ok": False, "error": {"code": "unknown_tool"}}
        )

    def test_string_argument(self):
        result = dispatch({
            "tool": "add",
            "arguments": {"a": "hello", "b": 3}
        })
        self.assertFalse(result["ok"])
        self.assertEqual(result["error"]["code"], "invalid_arguments")

    def test_boolean_argument(self):
        result = dispatch({
            "tool": "add",
            "arguments": {"a": True, "b": 3}
        })
        self.assertFalse(result["ok"])
        self.assertEqual(result["error"]["code"], "invalid_arguments")

    def test_missing_argument(self):
        result = dispatch({
            "tool": "add",
            "arguments": {"a": 2}
        })
        self.assertFalse(result["ok"])
        self.assertEqual(result["error"]["code"], "invalid_arguments")

    def test_failed_call_does_not_execute_another_tool(self):
        add_mock = Mock(return_value=5)
        multiply_mock = Mock(return_value=6)

        with patch("example.TOOLS", {
            "add": add_mock,
            "multiply": multiply_mock,
        }):
            result = dispatch({
                "tool": "unknown",
                "arguments": {"a": 2, "b": 3}
            })

        self.assertFalse(result["ok"])
        add_mock.assert_not_called()
        multiply_mock.assert_not_called()


if __name__ == "__main__":
    unittest.main()
