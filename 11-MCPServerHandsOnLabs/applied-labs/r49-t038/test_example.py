"""
Unit and Contract Tests for MCP Hands-On Labs Tool Dispatch, Failure & Recovery (R49-T038).
"""

import os
import sys
import unittest

# Ensure current directory is on sys.path for direct imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from example import (
    FailureRecoveryToolDispatcher,
    METHOD_NOT_FOUND,
    INVALID_PARAMS,
    exercise_failure_and_recovery,
)


class TestFailureRecoveryToolDispatcher(unittest.TestCase):
    """Test suite verifying contract execution, error envelopes, and recovery behavior."""

    def setUp(self):
        self.dispatcher = FailureRecoveryToolDispatcher()

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
        req = {"jsonrpc": "2.0", "id": 3, "tool": "power", "params": {"a": 2, "b": 3}}
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

    def test_missing_data_parameter_structured_error(self):
        """Focus: missing required parameter 'b' yields structured error (-32602)."""
        req = {"jsonrpc": "2.0", "id": 5, "tool": "add", "params": {"a": 10}}
        resp = self.dispatcher.dispatch(req)
        self.assertEqual(resp.get("id"), 5)
        self.assertIn("error", resp)
        self.assertEqual(resp["error"]["code"], INVALID_PARAMS)
        self.assertIn("Missing required parameter 'b'", resp["error"]["message"])

    def test_failed_call_cannot_execute_another_tool(self):
        """Contract: a failed call cannot execute another tool (zero side effects)."""
        # Failed call due to unknown tool
        req_unknown = {"jsonrpc": "2.0", "id": 6, "tool": "invalid_op", "params": {"a": 1, "b": 1}}
        self.dispatcher.dispatch(req_unknown)

        # Failed call due to missing parameter
        req_missing = {"jsonrpc": "2.0", "id": 7, "tool": "multiply", "params": {"a": 5}}
        self.dispatcher.dispatch(req_missing)

        # Failed call due to string parameter
        req_string = {"jsonrpc": "2.0", "id": 8, "tool": "add", "params": {"a": "test", "b": 2}}
        self.dispatcher.dispatch(req_string)

        # Verify no tool counters were modified
        self.assertEqual(self.dispatcher.get_tool_call_count("add"), 0)
        self.assertEqual(self.dispatcher.get_tool_call_count("multiply"), 0)
        self.assertEqual(sum(self.dispatcher.execution_counts.values()), 0)

    def test_failure_and_recovery_sequence(self):
        """Focus: exercise documented failure cases and verify clean recovery on subsequent valid call."""
        steps = exercise_failure_and_recovery(self.dispatcher)
        self.assertEqual(len(steps), 4)

        # Step 1: Baseline valid call
        self.assertTrue(steps[0].is_success)
        self.assertEqual(steps[0].response.get("result", {}).get("value"), 5)

        # Step 2: Documented missing-data failure
        self.assertFalse(steps[1].is_success)
        self.assertEqual(steps[1].response.get("error", {}).get("code"), INVALID_PARAMS)
        self.assertIn("Missing required parameter 'b'", steps[1].response["error"]["message"])

        # Step 3: Documented invalid-type failure
        self.assertFalse(steps[2].is_success)
        self.assertEqual(steps[2].response.get("error", {}).get("code"), INVALID_PARAMS)
        self.assertIn("must be numeric", steps[2].response["error"]["message"])

        # Step 4: Immediate clean recovery on next valid input
        self.assertTrue(steps[3].is_success)
        self.assertEqual(steps[3].response.get("result", {}).get("value"), 6)

    def test_deliberate_wrong_result_makes_test_fail(self):
        """Ensure test framework fails when a deliberate wrong result is introduced."""
        req = {"jsonrpc": "2.0", "id": 99, "tool": "multiply", "params": {"a": 2, "b": 3}}
        resp = self.dispatcher.dispatch(req)
        # 2 * 3 = 6; asserting 999 must raise AssertionError
        with self.assertRaises(AssertionError):
            self.assertEqual(resp.get("result", {}).get("value"), 999)


if __name__ == "__main__":
    unittest.main()
