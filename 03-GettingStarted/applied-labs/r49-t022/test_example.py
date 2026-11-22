"""
Unit tests for Applied Lab R49-T022: Local JSON Tool Dispatch with Allowlist and Validation.
"""

import unittest
from example import LocalToolDispatcher, CalculatorTools, ToolResponse, ToolError


class TestLocalToolDispatcher(unittest.TestCase):
    def setUp(self):
        self.tools = CalculatorTools()
        self.dispatcher = LocalToolDispatcher(tools=self.tools)

    def test_add_normal_valid(self):
        """Verify add(2, 3) -> 5 with success status and no error."""
        call = {"tool": "add", "arguments": {"a": 2, "b": 3}}
        resp = self.dispatcher.dispatch(call)

        self.assertTrue(resp.success)
        self.assertEqual(resp.tool, "add")
        self.assertEqual(resp.result, 5)
        self.assertIsNone(resp.error)
        self.assertEqual(self.tools.add_call_count, 1)
        self.assertEqual(self.tools.multiply_call_count, 0)

    def test_multiply_normal_valid(self):
        """Verify multiply(2, 3) -> 6 with success status and no error."""
        call = {"tool": "multiply", "arguments": {"a": 2, "b": 3}}
        resp = self.dispatcher.dispatch(call)

        self.assertTrue(resp.success)
        self.assertEqual(resp.tool, "multiply")
        self.assertEqual(resp.result, 6)
        self.assertIsNone(resp.error)
        self.assertEqual(self.tools.multiply_call_count, 1)
        self.assertEqual(self.tools.add_call_count, 0)

    def test_smallest_valid_boundaries(self):
        """Verify smallest valid boundary cases (zero, unity, floats, negatives)."""
        # Additive identity boundary
        res_zero = self.dispatcher.dispatch({"tool": "add", "arguments": {"a": 0, "b": 0}})
        self.assertTrue(res_zero.success)
        self.assertEqual(res_zero.result, 0)

        # Multiplicative identity boundary
        res_one = self.dispatcher.dispatch({"tool": "multiply", "arguments": {"a": 1, "b": 1}})
        self.assertTrue(res_one.success)
        self.assertEqual(res_one.result, 1)

        # Float and negative numbers
        res_float = self.dispatcher.dispatch({"tool": "add", "arguments": {"a": -2.5, "b": 10.5}})
        self.assertTrue(res_float.success)
        self.assertEqual(res_float.result, 8.0)

    def test_unknown_tool_returns_structured_error(self):
        """Verify unknown tool returns structured error and executes no handler."""
        call = {"tool": "divide", "arguments": {"a": 10, "b": 2}}
        resp = self.dispatcher.dispatch(call)

        self.assertFalse(resp.success)
        self.assertEqual(resp.tool, "divide")
        self.assertIsNone(resp.result)
        self.assertIsNotNone(resp.error)
        self.assertEqual(resp.error.code, "UNKNOWN_TOOL")
        self.assertIn("not in the allowlist", resp.error.message)
        # Ensure zero handler invocations
        self.assertEqual(self.tools.add_call_count, 0)
        self.assertEqual(self.tools.multiply_call_count, 0)

    def test_string_argument_returns_structured_error(self):
        """Verify string argument 'a' returns structured error and executes no tool."""
        call = {"tool": "add", "arguments": {"a": "2", "b": 3}}
        resp = self.dispatcher.dispatch(call)

        self.assertFalse(resp.success)
        self.assertEqual(resp.tool, "add")
        self.assertIsNone(resp.result)
        self.assertIsNotNone(resp.error)
        self.assertEqual(resp.error.code, "INVALID_ARGUMENT")
        self.assertIn("Argument 'a' must be a numeric value", resp.error.message)
        # Guarantee no execution occurred
        self.assertEqual(self.tools.add_call_count, 0)
        self.assertEqual(self.tools.multiply_call_count, 0)

    def test_boolean_argument_boundary_rejected(self):
        """Boundary decision: boolean values (e.g. True/False) must be strictly rejected."""
        call = {"tool": "multiply", "arguments": {"a": True, "b": 4}}
        resp = self.dispatcher.dispatch(call)

        self.assertFalse(resp.success)
        self.assertEqual(resp.error.code, "INVALID_ARGUMENT")
        self.assertEqual(self.tools.multiply_call_count, 0)

    def test_missing_argument_returns_structured_error(self):
        """Verify missing argument 'b' produces MISSING_ARGUMENT error."""
        call = {"tool": "add", "arguments": {"a": 5}}
        resp = self.dispatcher.dispatch(call)

        self.assertFalse(resp.success)
        self.assertEqual(resp.error.code, "MISSING_ARGUMENT")
        self.assertEqual(self.tools.add_call_count, 0)

    def test_failed_call_cannot_execute_another_tool(self):
        """
        Verify isolation: a failed call halts execution immediately and
        cannot cascade or invoke any secondary tool in sequence.
        """
        batch = [
            {"tool": "invalid_tool", "arguments": {"a": 1, "b": 2}},
            {"tool": "add", "arguments": {"a": 2, "b": 3}},
        ]
        results = self.dispatcher.dispatch_batch(batch, stop_on_failure=True)

        self.assertEqual(len(results), 1)
        self.assertFalse(results[0].success)
        self.assertEqual(results[0].error.code, "UNKNOWN_TOOL")
        # Ensure 'add' in second position was never executed
        self.assertEqual(self.tools.add_call_count, 0)
        self.assertEqual(self.tools.multiply_call_count, 0)

    def test_json_string_input_parsing(self):
        """Verify dispatcher accepts serialized JSON string input."""
        json_str = '{"tool": "add", "arguments": {"a": 10, "b": 20}}'
        resp = self.dispatcher.dispatch(json_str)

        self.assertTrue(resp.success)
        self.assertEqual(resp.result, 30)

    def test_deliberate_wrong_result_fails_assertion(self):
        """
        Demonstrate that a deliberate wrong result makes assertions fail.
        This verifies that our tests are sensitive and genuine checks.
        """
        call = {"tool": "add", "arguments": {"a": 2, "b": 3}}
        resp = self.dispatcher.dispatch(call)

        with self.assertRaises(AssertionError):
            self.assertEqual(resp.result, 999)


if __name__ == "__main__":
    unittest.main()
