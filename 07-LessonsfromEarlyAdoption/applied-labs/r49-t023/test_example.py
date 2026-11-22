"""
Unit tests for Applied Lab R49-T023: Tool Dispatch with Comparative Verification.
"""

import unittest
from example import (
    LocalToolDispatcher,
    CalculatorTools,
    EXPECTED_RESULT_TABLE,
    independent_reference_calculate,
)


class TestLocalToolDispatcherWithComparison(unittest.TestCase):
    def setUp(self):
        self.tools = CalculatorTools()
        self.dispatcher = LocalToolDispatcher(tools=self.tools)

    def test_add_normal_valid(self):
        """Verify add(2, 3) -> 5 with success status."""
        resp = self.dispatcher.dispatch({"tool": "add", "arguments": {"a": 2, "b": 3}})
        self.assertTrue(resp.success)
        self.assertEqual(resp.result, 5)
        self.assertIsNone(resp.error)
        self.assertEqual(self.tools.add_call_count, 1)

    def test_multiply_normal_valid(self):
        """Verify multiply(2, 3) -> 6 with success status."""
        resp = self.dispatcher.dispatch({"tool": "multiply", "arguments": {"a": 2, "b": 3}})
        self.assertTrue(resp.success)
        self.assertEqual(resp.result, 6)
        self.assertIsNone(resp.error)
        self.assertEqual(self.tools.multiply_call_count, 1)

    def test_unknown_tool_returns_structured_error(self):
        """Verify unknown tool returns structured error and executes no handler."""
        resp = self.dispatcher.dispatch({"tool": "subtract", "arguments": {"a": 5, "b": 2}})
        self.assertFalse(resp.success)
        self.assertIsNone(resp.result)
        self.assertIsNotNone(resp.error)
        self.assertEqual(resp.error.code, "UNKNOWN_TOOL")
        self.assertEqual(self.tools.add_call_count, 0)
        self.assertEqual(self.tools.multiply_call_count, 0)

    def test_string_argument_a_returns_structured_error(self):
        """Verify string argument 'a' returns structured error and executes no handler."""
        resp = self.dispatcher.dispatch({"tool": "add", "arguments": {"a": "2", "b": 3}})
        self.assertFalse(resp.success)
        self.assertIsNone(resp.result)
        self.assertIsNotNone(resp.error)
        self.assertEqual(resp.error.code, "INVALID_ARGUMENT")
        self.assertIn("must be a numeric value", resp.error.message)
        self.assertEqual(self.tools.add_call_count, 0)

    def test_boolean_argument_strictly_rejected(self):
        """Boundary verification: boolean types are strictly rejected."""
        resp = self.dispatcher.dispatch({"tool": "multiply", "arguments": {"a": False, "b": 10}})
        self.assertFalse(resp.success)
        self.assertEqual(resp.error.code, "INVALID_ARGUMENT")
        self.assertEqual(self.tools.multiply_call_count, 0)

    def test_failed_call_cannot_execute_another_tool(self):
        """
        Verify isolation: a failed call halts execution immediately and
        cannot cascade or execute subsequent tools in sequence.
        """
        calls = [
            {"tool": "unknown_tool", "arguments": {"a": 1, "b": 2}},
            {"tool": "add", "arguments": {"a": 10, "b": 20}},
        ]
        results = self.dispatcher.dispatch_batch(calls, stop_on_failure=True)
        self.assertEqual(len(results), 1)
        self.assertFalse(results[0].success)
        self.assertEqual(self.tools.add_call_count, 0)

    def test_compare_with_independent_reference_calculation(self):
        """
        Focus verification: compare direct implementation output against
        independent reference calculation oracle across multiple inputs.
        """
        test_inputs = [
            ("add", 2, 3),
            ("multiply", 2, 3),
            ("add", 0, 0),
            ("multiply", 1, 1),
            ("add", -10, 25),
            ("multiply", -3, 4),
        ]
        for tool, a, b in test_inputs:
            call = {"tool": tool, "arguments": {"a": a, "b": b}}
            cmp_rec = self.dispatcher.compare_with_reference(call)
            self.assertTrue(cmp_rec.agrees, f"Mismatch for {tool}({a}, {b})")
            self.assertEqual(cmp_rec.dispatcher_result, independent_reference_calculate(tool, a, b))

    def test_compare_with_explicit_expected_result_table(self):
        """
        Focus verification: compare direct implementation against the explicit
        predefined expected-result truth table using identical inputs.
        """
        for item in EXPECTED_RESULT_TABLE:
            call = {"tool": item["tool"], "arguments": item["arguments"]}
            resp = self.dispatcher.dispatch(call)
            self.assertTrue(resp.success)
            self.assertEqual(resp.result, item["expected_result"], f"Failed for {item}")

    def test_deliberate_wrong_result_fails_assertion(self):
        """Demonstrate that a deliberate wrong result makes assertions fail."""
        resp = self.dispatcher.dispatch({"tool": "add", "arguments": {"a": 2, "b": 3}})
        with self.assertRaises(AssertionError):
            self.assertEqual(resp.result, 1337)


if __name__ == "__main__":
    unittest.main()
