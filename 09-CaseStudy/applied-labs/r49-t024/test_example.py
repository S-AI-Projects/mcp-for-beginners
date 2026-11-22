"""
Unit tests for Applied Lab R49-T024: Intermediate State Trace & Invariant Verification.
"""

import unittest
from example import (
    LocalToolDispatcher,
    CalculatorTools,
    DispatchStage,
    InvariantVerifier,
    ToolResponse,
    ToolError,
    StepRecord,
)


class TestToolDispatcherWithStateInvariants(unittest.TestCase):
    def setUp(self):
        self.tools = CalculatorTools()
        self.dispatcher = LocalToolDispatcher(tools=self.tools)

    def test_add_normal_valid(self):
        """Verify add(2, 3) -> 5, complete state sequence, and invariant holds."""
        resp = self.dispatcher.dispatch({"tool": "add", "arguments": {"a": 2, "b": 3}})
        self.assertTrue(resp.success)
        self.assertEqual(resp.result, 5)
        self.assertIsNone(resp.error)
        self.assertEqual(self.tools.add_call_count, 1)

        # Invariant test
        self.assertTrue(InvariantVerifier.verify(resp))

        # Test intermediate stages sequence
        stages = [s.stage for s in resp.state_trace]
        expected_stages = [
            DispatchStage.INITIALIZED.value,
            DispatchStage.PARSED.value,
            DispatchStage.ALLOWLIST_CHECKED.value,
            DispatchStage.SCHEMA_VALIDATED.value,
            DispatchStage.DISPATCHING.value,
            DispatchStage.EXECUTED.value,
        ]
        self.assertEqual(stages, expected_stages)

    def test_multiply_normal_valid(self):
        """Verify multiply(2, 3) -> 6, complete state sequence, and invariant holds."""
        resp = self.dispatcher.dispatch({"tool": "multiply", "arguments": {"a": 2, "b": 3}})
        self.assertTrue(resp.success)
        self.assertEqual(resp.result, 6)
        self.assertIsNone(resp.error)
        self.assertEqual(self.tools.multiply_call_count, 1)
        self.assertTrue(InvariantVerifier.verify(resp))

    def test_unknown_tool_structured_error_and_state(self):
        """Verify unknown tool returns structured error and halts at ALLOWLIST_CHECKED."""
        resp = self.dispatcher.dispatch({"tool": "divide", "arguments": {"a": 10, "b": 2}})
        self.assertFalse(resp.success)
        self.assertIsNone(resp.result)
        self.assertIsNotNone(resp.error)
        self.assertEqual(resp.error.code, "UNKNOWN_TOOL")
        self.assertEqual(self.tools.add_call_count, 0)
        self.assertEqual(self.tools.multiply_call_count, 0)

        # Verify state trace halted at ALLOWLIST_CHECKED with FAILURE
        self.assertEqual(resp.state_trace[-1].stage, DispatchStage.ALLOWLIST_CHECKED.value)
        self.assertEqual(resp.state_trace[-1].status, "FAILURE")
        self.assertNotIn(DispatchStage.EXECUTED.value, [s.stage for s in resp.state_trace])

        # Invariant test
        self.assertTrue(InvariantVerifier.verify(resp))

    def test_string_argument_a_structured_error_and_state(self):
        """Verify string 'a' produces INVALID_ARGUMENT and halts at SCHEMA_VALIDATED."""
        resp = self.dispatcher.dispatch({"tool": "add", "arguments": {"a": "2", "b": 3}})
        self.assertFalse(resp.success)
        self.assertIsNone(resp.result)
        self.assertIsNotNone(resp.error)
        self.assertEqual(resp.error.code, "INVALID_ARGUMENT")
        self.assertEqual(self.tools.add_call_count, 0)

        # Verify state trace halted at SCHEMA_VALIDATED with FAILURE
        self.assertEqual(resp.state_trace[-1].stage, DispatchStage.SCHEMA_VALIDATED.value)
        self.assertEqual(resp.state_trace[-1].status, "FAILURE")
        self.assertNotIn(DispatchStage.EXECUTED.value, [s.stage for s in resp.state_trace])

        # Invariant test
        self.assertTrue(InvariantVerifier.verify(resp))

    def test_boolean_argument_strictly_rejected(self):
        """Verify boolean types are strictly rejected as invalid numeric arguments."""
        resp = self.dispatcher.dispatch({"tool": "multiply", "arguments": {"a": True, "b": 5}})
        self.assertFalse(resp.success)
        self.assertEqual(resp.error.code, "INVALID_ARGUMENT")
        self.assertEqual(self.tools.multiply_call_count, 0)
        self.assertTrue(InvariantVerifier.verify(resp))

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

    def test_invariant_violation_detection(self):
        """Verify that InvariantVerifier raises AssertionError if state invariants are broken."""
        # Simulated corrupt response: marked success but missing result
        corrupt_resp = ToolResponse(
            success=True,
            tool="add",
            result=None,
            state_trace=[
                StepRecord(step=1, stage=DispatchStage.INITIALIZED.value, status="SUCCESS", details={}),
                StepRecord(step=2, stage=DispatchStage.EXECUTED.value, status="SUCCESS", details={}),
            ]
        )
        with self.assertRaises(AssertionError):
            InvariantVerifier.verify(corrupt_resp)

    def test_deliberate_wrong_result_fails_assertion(self):
        """Demonstrate that a deliberate wrong result makes assertions fail."""
        resp = self.dispatcher.dispatch({"tool": "add", "arguments": {"a": 2, "b": 3}})
        with self.assertRaises(AssertionError):
            self.assertEqual(resp.result, 999)


if __name__ == "__main__":
    unittest.main()
