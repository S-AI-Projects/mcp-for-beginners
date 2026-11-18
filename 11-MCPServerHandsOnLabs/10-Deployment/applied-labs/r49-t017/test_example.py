"""Unit tests and regression checks for R49-T017 typed tool dispatch."""

import unittest

from example import dispatch_tool


class TestTypedToolDispatch(unittest.TestCase):
    """Test suite verifying tool allowlist, numeric validation, and structured errors."""

    def test_add_normal_case(self):
        """add(2, 3) returns 5 with success status."""
        res = dispatch_tool({"tool": "add", "arguments": {"a": 2, "b": 3}})
        self.assertTrue(res["success"])
        self.assertEqual(res["tool"], "add")
        self.assertEqual(res["result"], 5)

    def test_multiply_normal_case(self):
        """multiply(2, 3) returns 6 with success status."""
        res = dispatch_tool({"tool": "multiply", "arguments": {"a": 2, "b": 3}})
        self.assertTrue(res["success"])
        self.assertEqual(res["tool"], "multiply")
        self.assertEqual(res["result"], 6)

    def test_unknown_tool_returns_structured_error(self):
        """Unknown tool produces structured UNKNOWN_TOOL error envelope."""
        res = dispatch_tool({"tool": "divide", "arguments": {"a": 6, "b": 2}})
        self.assertFalse(res["success"])
        self.assertIn("error", res)
        self.assertEqual(res["error"]["code"], "UNKNOWN_TOOL")
        self.assertIn("not in allowlist", res["error"]["message"])

    def test_string_argument_a_returns_structured_error(self):
        """String 'a' returns structured INVALID_ARGUMENT_TYPE error without fallback."""
        res = dispatch_tool({"tool": "add", "arguments": {"a": "2", "b": 3}})
        self.assertFalse(res["success"])
        self.assertEqual(res["error"]["code"], "INVALID_ARGUMENT_TYPE")
        self.assertIn("Argument 'a' must be numeric", res["error"]["message"])

    def test_string_argument_b_returns_structured_error(self):
        """String 'b' returns structured INVALID_ARGUMENT_TYPE error."""
        res = dispatch_tool({"tool": "multiply", "arguments": {"a": 2, "b": "three"}})
        self.assertFalse(res["success"])
        self.assertEqual(res["error"]["code"], "INVALID_ARGUMENT_TYPE")

    def test_boolean_argument_rejected(self):
        """Boolean values (subclasses of int in Python) are rejected as numeric arguments."""
        res = dispatch_tool({"tool": "add", "arguments": {"a": True, "b": 3}})
        self.assertFalse(res["success"])
        self.assertEqual(res["error"]["code"], "INVALID_ARGUMENT_TYPE")

    def test_missing_argument_returns_structured_error(self):
        """Missing 'b' argument returns MISSING_ARGUMENT error."""
        res = dispatch_tool({"tool": "add", "arguments": {"a": 2}})
        self.assertFalse(res["success"])
        self.assertEqual(res["error"]["code"], "MISSING_ARGUMENT")

    def test_invalid_payload_type(self):
        """Non-dictionary payload returns INVALID_PAYLOAD error."""
        res = dispatch_tool("invalid payload")  # type: ignore
        self.assertFalse(res["success"])
        self.assertEqual(res["error"]["code"], "INVALID_PAYLOAD")


if __name__ == "__main__":
    unittest.main()
