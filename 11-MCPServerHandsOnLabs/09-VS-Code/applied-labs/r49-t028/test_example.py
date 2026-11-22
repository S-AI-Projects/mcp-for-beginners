"""
Unit tests for Applied Lab R49-T028: Error Explanation and Next-Input Recovery.
"""

import unittest
from example import (
    VSCodeToolDispatcher,
    CalculatorTools,
    run_recovery_demonstration,
)


class TestVSCodeErrorExplanationAndRecovery(unittest.TestCase):
    def setUp(self):
        self.tools = CalculatorTools()
        self.dispatcher = VSCodeToolDispatcher(tools=self.tools)

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

    def test_unknown_tool_structured_error(self):
        """Verify unknown tool produces UNKNOWN_TOOL error and halts."""
        resp = self.dispatcher.dispatch({"tool": "delete_database", "arguments": {"a": 1, "b": 2}})
        self.assertFalse(resp.success)
        self.assertEqual(resp.error.code, "UNKNOWN_TOOL")
        self.assertEqual(self.tools.add_call_count, 0)
        self.assertEqual(self.tools.multiply_call_count, 0)

    def test_string_argument_a_structured_error(self):
        """Verify string argument 'a' produces INVALID_ARGUMENT error with diagnostic details."""
        resp = self.dispatcher.dispatch({"tool": "add", "arguments": {"a": "two", "b": 3}})
        self.assertFalse(resp.success)
        self.assertEqual(resp.error.code, "INVALID_ARGUMENT")
        self.assertIn("must be a numeric value", resp.error.message)
        self.assertIn("remediation", resp.error.details)
        self.assertEqual(self.tools.add_call_count, 0)

    def test_boolean_argument_strictly_rejected(self):
        """Verify boolean values are rejected as invalid arguments."""
        resp = self.dispatcher.dispatch({"tool": "multiply", "arguments": {"a": True, "b": 4}})
        self.assertFalse(resp.success)
        self.assertEqual(resp.error.code, "INVALID_ARGUMENT")
        self.assertEqual(self.tools.multiply_call_count, 0)

    def test_missing_data_exercised_and_explained(self):
        """
        Focus test: Exercise documented missing-data case and verify structured explanation.
        """
        missing_call = {"tool": "add", "arguments": {"a": 2}}
        resp = self.dispatcher.dispatch(missing_call)

        self.assertFalse(resp.success)
        self.assertIsNone(resp.result)
        self.assertEqual(resp.error.code, "MISSING_ARGUMENT")
        self.assertIn("Missing required numeric parameter 'b'", resp.error.message)
        self.assertEqual(resp.error.details["missing_parameter"], "b")
        self.assertIn("remediation", resp.error.details)
        self.assertEqual(self.tools.add_call_count, 0)

    def test_demonstrate_recovery_on_next_valid_input(self):
        """
        Focus test: Exercise invalid/missing data, verify error, then demonstrate clean recovery.
        """
        # Turn 1: Missing 'b'
        err_resp1 = self.dispatcher.dispatch({"tool": "add", "arguments": {"a": 2}})
        self.assertFalse(err_resp1.success)
        self.assertEqual(err_resp1.error.code, "MISSING_ARGUMENT")

        # Turn 2: Client recovers on next input
        rec_resp1 = self.dispatcher.dispatch({"tool": "add", "arguments": {"a": 2, "b": 3}})
        self.assertTrue(rec_resp1.success)
        self.assertEqual(rec_resp1.result, 5)

        # Turn 3: Invalid string 'a'
        err_resp2 = self.dispatcher.dispatch({"tool": "multiply", "arguments": {"a": "2", "b": 3}})
        self.assertFalse(err_resp2.success)
        self.assertEqual(err_resp2.error.code, "INVALID_ARGUMENT")

        # Turn 4: Client recovers on next input
        rec_resp2 = self.dispatcher.dispatch({"tool": "multiply", "arguments": {"a": 2, "b": 3}})
        self.assertTrue(rec_resp2.success)
        self.assertEqual(rec_resp2.result, 6)

    def test_recovery_demonstration_helper(self):
        """Verify the full recovery demonstration scenario execution."""
        history = run_recovery_demonstration()
        self.assertEqual(len(history), 4)
        self.assertEqual(history[0]["status"], "REJECTED_WITH_EXPLANATION")
        self.assertEqual(history[1]["status"], "SUCCESS")
        self.assertEqual(history[2]["status"], "REJECTED_WITH_EXPLANATION")
        self.assertEqual(history[3]["status"], "SUCCESS")

    def test_failed_call_cannot_execute_another_tool(self):
        """Verify isolation: failed call halts batch immediately."""
        calls = [
            {"tool": "forbidden_tool", "arguments": {"a": 1, "b": 2}},
            {"tool": "add", "arguments": {"a": 2, "b": 3}}
        ]
        batch = self.dispatcher.dispatch_batch(calls, stop_on_failure=True)
        self.assertEqual(len(batch), 1)
        self.assertFalse(batch[0].success)
        self.assertEqual(self.tools.add_call_count, 0)

    def test_deliberate_wrong_result_fails_assertion(self):
        """Demonstrate that a deliberate wrong result makes assertions fail."""
        res = self.dispatcher.dispatch({"tool": "add", "arguments": {"a": 2, "b": 3}})
        with self.assertRaises(AssertionError):
            self.assertEqual(res.result, 999)


if __name__ == "__main__":
    unittest.main()
