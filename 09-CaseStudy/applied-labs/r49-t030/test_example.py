"""
Unit tests for Local Tool Contract Dispatcher and Applied Questions.
Validates R49-T030 contract and question verifiers.
"""

import unittest

try:
    from .example import (
        LocalContractDispatcher,
        get_applied_questions,
        verify_question_1,
        verify_question_2,
        verify_question_3,
    )
except ImportError:
    from example import (
        LocalContractDispatcher,
        get_applied_questions,
        verify_question_1,
        verify_question_2,
        verify_question_3,
    )


class TestAppliedQuestionsDispatcher(unittest.TestCase):
    """Test suite covering contract dispatch and applied question verification."""

    def setUp(self) -> None:
        self.dispatcher = LocalContractDispatcher()
        self.questions = {q.question_id: q for q in get_applied_questions()}

    def test_baseline_contract_add(self) -> None:
        """add(2, 3) -> 5"""
        payload = {"tool": "add", "arguments": {"a": 2, "b": 3}}
        res = self.dispatcher.dispatch(payload)
        self.assertEqual(res, {"status": "success", "result": 5})
        self.assertEqual(self.dispatcher.execution_counts["add"], 1)

    def test_baseline_contract_multiply(self) -> None:
        """multiply(2, 3) -> 6"""
        payload = {"tool": "multiply", "arguments": {"a": 2, "b": 3}}
        res = self.dispatcher.dispatch(payload)
        self.assertEqual(res, {"status": "success", "result": 6})
        self.assertEqual(self.dispatcher.execution_counts["multiply"], 1)

    def test_unknown_tool_structured_error(self) -> None:
        """Unknown tool returns structured error without executing any tool."""
        payload = {"tool": "subtract", "arguments": {"a": 5, "b": 2}}
        res = self.dispatcher.dispatch(payload)
        self.assertEqual(res["status"], "error")
        self.assertEqual(res["error"]["code"], "UNKNOWN_TOOL")
        self.assertEqual(self.dispatcher.execution_counts["add"], 0)
        self.assertEqual(self.dispatcher.execution_counts["multiply"], 0)

    def test_string_argument_structured_error(self) -> None:
        """String argument 'a' returns structured error without executing tool."""
        payload = {"tool": "add", "arguments": {"a": "2", "b": 3}}
        res = self.dispatcher.dispatch(payload)
        self.assertEqual(res["status"], "error")
        self.assertEqual(res["error"]["code"], "INVALID_ARGUMENT")
        self.assertEqual(res["error"]["parameter"], "a")
        self.assertEqual(self.dispatcher.execution_counts["add"], 0)
        self.assertEqual(self.dispatcher.execution_counts["multiply"], 0)

    def test_failed_call_cannot_execute_another_tool(self) -> None:
        """A failure in add does not trigger multiply or invoke handlers."""
        counts_before = dict(self.dispatcher.execution_counts)
        payload = {"tool": "add", "arguments": {"a": "invalid", "b": 10}}
        res = self.dispatcher.dispatch(payload)
        self.assertEqual(res["status"], "error")
        self.assertEqual(self.dispatcher.execution_counts, counts_before)

    def test_applied_question_1_predict_output(self) -> None:
        """Verifies Question 1 executable check passes against dispatcher."""
        q1 = self.questions["Q1_PREDICT_OUTPUT"]
        self.assertTrue(verify_question_1(self.dispatcher, q1))

    def test_applied_question_2_diagnose_failure(self) -> None:
        """Verifies Question 2 executable check passes against dispatcher."""
        q2 = self.questions["Q2_DIAGNOSE_FAILURE"]
        self.assertTrue(verify_question_2(self.dispatcher, q2))

    def test_applied_question_3_choose_boundary_policy(self) -> None:
        """Verifies Question 3 executable check passes against dispatcher."""
        q3 = self.questions["Q3_BOUNDARY_POLICY"]
        self.assertTrue(verify_question_3(self.dispatcher, q3))

    def test_missing_argument_handling(self) -> None:
        """Missing parameter triggers structured error."""
        payload = {"tool": "multiply", "arguments": {"a": 4}}
        res = self.dispatcher.dispatch(payload)
        self.assertEqual(res["status"], "error")
        self.assertEqual(res["error"]["code"], "MISSING_ARGUMENT")


if __name__ == "__main__":
    unittest.main()
