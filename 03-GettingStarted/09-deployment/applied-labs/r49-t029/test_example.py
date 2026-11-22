"""
Unit tests for Applied Lab R49-T029: Tool Dispatch and Deployment Configuration Benchmarking.
"""

import unittest
from example import (
    ConfigurableToolDispatcher,
    CalculatorTools,
    PROFILES,
    benchmark_configurations,
)


class TestConfigurableDeploymentDispatch(unittest.TestCase):
    def setUp(self):
        self.tools = CalculatorTools()
        self.dispatcher = ConfigurableToolDispatcher(tools=self.tools)

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
        """Verify unknown tool returns structured error and halts."""
        resp = self.dispatcher.dispatch({"tool": "unknown_tool", "arguments": {"a": 1, "b": 2}})
        self.assertFalse(resp.success)
        self.assertEqual(resp.error.code, "UNKNOWN_TOOL")
        self.assertEqual(self.tools.add_call_count, 0)
        self.assertEqual(self.tools.multiply_call_count, 0)

    def test_string_argument_a_structured_error(self):
        """Verify string argument 'a' returns structured error."""
        resp = self.dispatcher.dispatch({"tool": "add", "arguments": {"a": "2", "b": 3}})
        self.assertFalse(resp.success)
        self.assertEqual(resp.error.code, "INVALID_ARGUMENT")
        self.assertEqual(self.tools.add_call_count, 0)

    def test_boolean_argument_strictly_rejected(self):
        """Verify boolean types are rejected as invalid arguments."""
        resp = self.dispatcher.dispatch({"tool": "multiply", "arguments": {"a": True, "b": 5}})
        self.assertFalse(resp.success)
        self.assertEqual(resp.error.code, "INVALID_ARGUMENT")
        self.assertEqual(self.tools.multiply_call_count, 0)

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

    def test_compare_three_controlled_configurations(self):
        """
        Focus test: Compare three controlled configurations, verify 100% correctness,
        and validate the observed memory/telemetry trade-off.
        """
        metrics = benchmark_configurations(call_count=30)
        self.assertEqual(len(metrics), 3)

        keys = [m["profile_key"] for m in metrics]
        self.assertEqual(keys, ["minimal", "standard", "diagnostic"])

        for m in metrics:
            # Correctness must be 100% across all configs
            self.assertEqual(m["correctness_percentage"], 100.0)
            self.assertEqual(m["correct_calls"], m["total_calls"])

        # Minimal configuration must retain 0 records in memory
        self.assertEqual(metrics[0]["retained_memory_records"], 0)
        # Standard configuration retains bounded records
        self.assertGreater(metrics[1]["retained_memory_records"], 0)
        # Diagnostic retains telemetry
        self.assertGreater(metrics[2]["retained_memory_records"], 0)

    def test_deliberate_wrong_result_fails_assertion(self):
        """Demonstrate that a deliberate wrong result makes assertions fail."""
        resp = self.dispatcher.dispatch({"tool": "add", "arguments": {"a": 2, "b": 3}})
        with self.assertRaises(AssertionError):
            self.assertEqual(resp.result, 999)


if __name__ == "__main__":
    unittest.main()
