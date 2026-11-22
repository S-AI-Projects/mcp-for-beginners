"""
Unit and Contract Tests for MCP Best Practices Tool Dispatch & Applied Questions (R49-T037).
"""

import os
import sys
import unittest

# Ensure current directory is on sys.path for direct imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from example import (
    BestPracticesToolDispatcher,
    METHOD_NOT_FOUND,
    INVALID_PARAMS,
    APPLIED_QUESTIONS,
    check_q1_predict_output,
    check_q2_diagnose_failure,
    check_q3_boundary_policy,
)


class TestBestPracticesToolDispatcher(unittest.TestCase):
    """Test suite verifying contract execution, error envelopes, and applied questions."""

    def setUp(self):
        self.dispatcher = BestPracticesToolDispatcher()

    def test_add_operation_valid(self):
        """Contract: add(2,3) -> 5."""
        req = {"jsonrpc": "2.0", "id": 1, "tool": "add", "params": {"a": 2, "b": 3}}
        resp = self.dispatcher.dispatch(req)
        self.assertEqual(resp.get("id"), 1)
        self.assertNotIn("error", resp)
        self.assertEqual(resp.get("result", {}).get("value"), 5)
        self.assertEqual(self.dispatcher.get_tool_call_count("add"), 1)

    def test_multiply_operation_valid(self):
        """Contract: multiply(2,3) -> 6."""
        req = {"jsonrpc": "2.0", "id": 2, "tool": "multiply", "params": {"a": 2, "b": 3}}
        resp = self.dispatcher.dispatch(req)
        self.assertEqual(resp.get("id"), 2)
        self.assertNotIn("error", resp)
        self.assertEqual(resp.get("result", {}).get("value"), 6)
        self.assertEqual(self.dispatcher.get_tool_call_count("multiply"), 1)

    def test_unknown_tool_structured_error(self):
        """Contract: unknown tool yields structured error (-32601)."""
        req = {"jsonrpc": "2.0", "id": 3, "tool": "subtract", "params": {"a": 5, "b": 2}}
        resp = self.dispatcher.dispatch(req)
        self.assertEqual(resp.get("id"), 3)
        self.assertIn("error", resp)
        self.assertEqual(resp["error"]["code"], METHOD_NOT_FOUND)
        self.assertIn("not allowlisted", resp["error"]["message"])

    def test_string_parameter_structured_error(self):
        """Contract: string 'a' yields structured error (-32602)."""
        req = {"jsonrpc": "2.0", "id": 4, "tool": "add", "params": {"a": "2", "b": 3}}
        resp = self.dispatcher.dispatch(req)
        self.assertEqual(resp.get("id"), 4)
        self.assertIn("error", resp)
        self.assertEqual(resp["error"]["code"], INVALID_PARAMS)
        self.assertIn("must be numeric", resp["error"]["message"])

    def test_failed_call_cannot_execute_another_tool(self):
        """Contract: a failed call cannot execute another tool (zero side effects)."""
        # Failed call due to unknown tool
        req_bad_tool = {"jsonrpc": "2.0", "id": 5, "tool": "unknown_tool", "params": {"a": 1, "b": 1}}
        self.dispatcher.dispatch(req_bad_tool)

        # Failed call due to invalid param
        req_bad_arg = {"jsonrpc": "2.0", "id": 6, "tool": "multiply", "params": {"a": "invalid", "b": 2}}
        self.dispatcher.dispatch(req_bad_arg)

        # Verify no tool counter was incremented
        self.assertEqual(self.dispatcher.get_tool_call_count("add"), 0)
        self.assertEqual(self.dispatcher.get_tool_call_count("multiply"), 0)
        self.assertEqual(sum(self.dispatcher.execution_counts.values()), 0)

    def test_boolean_rejected_as_numeric(self):
        """Ensure boolean values (subclass of int in Python) are rejected as invalid params."""
        req = {"jsonrpc": "2.0", "id": 7, "tool": "add", "params": {"a": True, "b": 3}}
        resp = self.dispatcher.dispatch(req)
        self.assertIn("error", resp)
        self.assertEqual(resp["error"]["code"], INVALID_PARAMS)

    def test_q1_predict_output_executable_check(self):
        """Verify Applied Question 1 (Predict output of add(2.5, -0.5))."""
        self.assertTrue(check_q1_predict_output())
        q1 = APPLIED_QUESTIONS[0]
        self.assertEqual(q1.category, "Predict an Output")
        self.assertEqual(q1.factual_answer["result"]["value"], 2.0)

    def test_q2_diagnose_failure_executable_check(self):
        """Verify Applied Question 2 (Diagnose failure on multiply('3', 4))."""
        self.assertTrue(check_q2_diagnose_failure())
        q2 = APPLIED_QUESTIONS[1]
        self.assertEqual(q2.category, "Diagnose a Failure")
        self.assertEqual(q2.factual_answer["error_code"], -32602)
        self.assertEqual(q2.factual_answer["handlers_executed"], 0)

    def test_q3_boundary_policy_executable_check(self):
        """Verify Applied Question 3 (Boundary policy for unallowlisted tool)."""
        self.assertTrue(check_q3_boundary_policy())
        q3 = APPLIED_QUESTIONS[2]
        self.assertEqual(q3.category, "Choose a Boundary Policy")
        self.assertEqual(q3.factual_answer, "REJECT_IMMEDIATELY_NO_FALLBACK")

    def test_deliberate_wrong_result_makes_test_fail(self):
        """Ensure test harness detects incorrect behavior (prevent silent false positives)."""
        req = {"jsonrpc": "2.0", "id": 99, "tool": "add", "params": {"a": 2, "b": 3}}
        resp = self.dispatcher.dispatch(req)
        # 2 + 3 is 5, asserting it equals 999 must raise AssertionError
        with self.assertRaises(AssertionError):
            self.assertEqual(resp.get("result", {}).get("value"), 999)


if __name__ == "__main__":
    unittest.main()
