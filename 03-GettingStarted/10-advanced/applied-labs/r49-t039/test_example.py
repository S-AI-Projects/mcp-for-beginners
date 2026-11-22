"""
Unit and Contract Tests for Advanced Low-Level Dispatch & Evaluation Experiment (R49-T039).
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from example import (
    AdvancedLowLevelDispatcher,
    METHOD_NOT_FOUND,
    INVALID_PARAMS,
    run_evaluation_experiment,
)


class TestAdvancedLowLevelDispatcher(unittest.TestCase):
    """Test suite verifying contract execution, error envelopes, and evaluation experiment."""

    def setUp(self):
        self.dispatcher = AdvancedLowLevelDispatcher()

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
        req = {"jsonrpc": "2.0", "id": 3, "tool": "unauthorized_cmd", "params": {"a": 1, "b": 1}}
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

    def test_circuit_isolation(self):
        """Contract: a failed call cannot execute another tool (zero side effects)."""
        req_bad1 = {"jsonrpc": "2.0", "id": 5, "tool": "system_exec", "params": {"a": 1, "b": 1}}
        self.dispatcher.dispatch(req_bad1)

        req_bad2 = {"jsonrpc": "2.0", "id": 6, "tool": "add", "params": {"a": "str", "b": 2}}
        self.dispatcher.dispatch(req_bad2)

        self.assertEqual(self.dispatcher.get_tool_call_count("add"), 0)
        self.assertEqual(self.dispatcher.get_tool_call_count("multiply"), 0)
        self.assertEqual(sum(self.dispatcher.execution_counts.values()), 0)

    def test_evaluation_experiment_configurations(self):
        """Focus: compare 3 controlled configurations, verify correctness & metrics."""
        metrics = run_evaluation_experiment()
        self.assertEqual(len(metrics), 3)

        # Config 1: Minimal single-call
        m1 = metrics[0]
        self.assertEqual(m1.input_size, 1)
        self.assertEqual(m1.valid_calls_passed, 1)
        self.assertEqual(m1.correctness_rate, 100.0)
        self.assertEqual(m1.unauthorized_tool_calls, 0)

        # Config 2: Standard dual-tool pair
        m2 = metrics[1]
        self.assertEqual(m2.input_size, 2)
        self.assertEqual(m2.valid_calls_passed, 2)
        self.assertEqual(m2.correctness_rate, 100.0)
        self.assertEqual(m2.unauthorized_tool_calls, 0)

        # Config 3: Mixed boundary batch
        m3 = metrics[2]
        self.assertEqual(m3.input_size, 6)
        self.assertEqual(m3.valid_calls_passed, 3)
        self.assertEqual(m3.invalid_calls_rejected, 3)
        self.assertEqual(m3.correctness_rate, 100.0)
        self.assertEqual(m3.unauthorized_tool_calls, 0)

    def test_deliberate_wrong_result_makes_test_fail(self):
        """Ensure test harness detects incorrect behavior (prevent silent false positives)."""
        req = {"jsonrpc": "2.0", "id": 99, "tool": "add", "params": {"a": 2, "b": 3}}
        resp = self.dispatcher.dispatch(req)
        # 2 + 3 is 5, asserting it equals 999 must raise AssertionError
        with self.assertRaises(AssertionError):
            self.assertEqual(resp.get("result", {}).get("value"), 999)


if __name__ == "__main__":
    unittest.main()
