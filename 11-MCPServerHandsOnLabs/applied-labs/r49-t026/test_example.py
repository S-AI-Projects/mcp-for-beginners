"""
Unit tests for Applied Lab R49-T026: Tool Dispatch Refactoring and Equivalence Proof.
"""

import unittest
from example import (
    BaselineToolDispatcher,
    RefactoredToolDispatcher,
    NumericArgumentValidator,
    CalculatorTools,
    SAMPLE_FIXTURES,
    prove_before_after_equivalence,
)


class TestDispatcherRefactoringAndEquivalence(unittest.TestCase):
    def setUp(self):
        self.baseline_tools = CalculatorTools()
        self.baseline = BaselineToolDispatcher(tools=self.baseline_tools)

        self.refactored_tools = CalculatorTools()
        self.refactored = RefactoredToolDispatcher(tools=self.refactored_tools)

    def test_add_normal_valid(self):
        """Verify add(2, 3) -> 5 on both baseline and refactored dispatchers."""
        call = {"tool": "add", "arguments": {"a": 2, "b": 3}}
        b_res = self.baseline.dispatch(call)
        r_res = self.refactored.dispatch(call)

        self.assertTrue(b_res.success)
        self.assertTrue(r_res.success)
        self.assertEqual(b_res.result, 5)
        self.assertEqual(r_res.result, 5)
        self.assertEqual(b_res.to_dict(), r_res.to_dict())

    def test_multiply_normal_valid(self):
        """Verify multiply(2, 3) -> 6 on both baseline and refactored dispatchers."""
        call = {"tool": "multiply", "arguments": {"a": 2, "b": 3}}
        b_res = self.baseline.dispatch(call)
        r_res = self.refactored.dispatch(call)

        self.assertTrue(b_res.success)
        self.assertTrue(r_res.success)
        self.assertEqual(b_res.result, 6)
        self.assertEqual(r_res.result, 6)
        self.assertEqual(b_res.to_dict(), r_res.to_dict())

    def test_unknown_tool_structured_error(self):
        """Verify unknown tool produces identical UNKNOWN_TOOL error on both."""
        call = {"tool": "divide", "arguments": {"a": 10, "b": 2}}
        b_res = self.baseline.dispatch(call)
        r_res = self.refactored.dispatch(call)

        self.assertFalse(b_res.success)
        self.assertFalse(r_res.success)
        self.assertEqual(b_res.error.code, "UNKNOWN_TOOL")
        self.assertEqual(r_res.error.code, "UNKNOWN_TOOL")
        self.assertEqual(self.baseline_tools.add_call_count, 0)
        self.assertEqual(self.refactored_tools.add_call_count, 0)

    def test_string_argument_a_structured_error(self):
        """Verify string argument 'a' produces identical INVALID_ARGUMENT error on both."""
        call = {"tool": "add", "arguments": {"a": "2", "b": 3}}
        b_res = self.baseline.dispatch(call)
        r_res = self.refactored.dispatch(call)

        self.assertFalse(b_res.success)
        self.assertFalse(r_res.success)
        self.assertEqual(b_res.error.code, "INVALID_ARGUMENT")
        self.assertEqual(r_res.error.code, "INVALID_ARGUMENT")
        self.assertEqual(b_res.to_dict(), r_res.to_dict())
        self.assertEqual(self.baseline_tools.add_call_count, 0)
        self.assertEqual(self.refactored_tools.add_call_count, 0)

    def test_boolean_argument_rejected_identically(self):
        """Verify boolean argument 'a' is rejected identically on both."""
        call = {"tool": "multiply", "arguments": {"a": True, "b": 5}}
        b_res = self.baseline.dispatch(call)
        r_res = self.refactored.dispatch(call)

        self.assertFalse(b_res.success)
        self.assertFalse(r_res.success)
        self.assertEqual(b_res.error.code, "INVALID_ARGUMENT")
        self.assertEqual(r_res.error.code, "INVALID_ARGUMENT")
        self.assertEqual(b_res.to_dict(), r_res.to_dict())

    def test_failed_call_cannot_execute_another_tool(self):
        """Verify isolation: failed call halts batch on both dispatchers."""
        calls = [
            {"tool": "forbidden_tool", "arguments": {"a": 1, "b": 2}},
            {"tool": "add", "arguments": {"a": 2, "b": 3}}
        ]
        b_batch = self.baseline.dispatch_batch(calls, stop_on_failure=True)
        r_batch = self.refactored.dispatch_batch(calls, stop_on_failure=True)

        self.assertEqual(len(b_batch), 1)
        self.assertEqual(len(r_batch), 1)
        self.assertEqual(self.baseline_tools.add_call_count, 0)
        self.assertEqual(self.refactored_tools.add_call_count, 0)

    def test_prove_before_after_equivalence(self):
        """Focus test: prove before/after equivalence across all fixtures."""
        results = prove_before_after_equivalence(SAMPLE_FIXTURES)
        self.assertEqual(len(results), len(SAMPLE_FIXTURES))
        for res in results:
            self.assertTrue(res["equivalent"])

    def test_equivalence_violation_detection(self):
        """Verify that an injected discrepancy breaks equivalence verification."""
        discrepant_fixture = [
            {"id": "bad_test", "call": {"tool": "add", "arguments": {"a": 2, "b": 3}}}
        ]
        # Temporarily mock refactored tools to return wrong result
        corrupt_tools = CalculatorTools()
        corrupt_tools.add = lambda a, b: 999
        corrupt_dispatcher = RefactoredToolDispatcher(tools=corrupt_tools)

        baseline_out = self.baseline.dispatch(discrepant_fixture[0]["call"]).to_dict()
        corrupt_out = corrupt_dispatcher.dispatch(discrepant_fixture[0]["call"]).to_dict()
        self.assertNotEqual(baseline_out, corrupt_out)

    def test_deliberate_wrong_result_fails_assertion(self):
        """Demonstrate that a deliberate wrong result makes assertions fail."""
        res = self.refactored.dispatch({"tool": "add", "arguments": {"a": 2, "b": 3}})
        with self.assertRaises(AssertionError):
            self.assertEqual(res.result, 999)


if __name__ == "__main__":
    unittest.main()
