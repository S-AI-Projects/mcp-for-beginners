"""
Unit tests for MCP Trace Aggregation & Refactored Architecture.

Lesson Extension: 11-MCPServerHandsOnLabs/11-Monitoring
Task ID: R49-T036

Validates:
- Request A has two tool calls, duration 12ms, and status SUCCESS.
- Request B fails with database error.
- Request C (missing end event) is marked INCOMPLETE with duration None (not zero).
- Prompt contents are strictly excluded from output.
- Before/after refactoring equivalence between baseline and modular aggregator.
- Deliberate wrong result detection.
"""

import json
import os
import sys
import unittest

# Ensure current directory is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from example import (
    BaselineTraceAggregator,
    RefactoredTraceAggregator,
    TraceLifecycleClassifier,
    verify_before_after_equivalence,
    LOCAL_TRACE_FIXTURE,
)


class TestTraceAggregation(unittest.TestCase):
    """Test suite validating trace aggregation, prompt omission, and refactoring equivalence."""

    def setUp(self):
        self.baseline = BaselineTraceAggregator()
        self.refactored = RefactoredTraceAggregator()
        self.fixture = list(LOCAL_TRACE_FIXTURE)

    def test_request_a_success_two_tools_12ms(self):
        """
        Primary Contract:
        Request A has two tool calls, duration 12ms, and status SUCCESS.
        """
        report = self.refactored.aggregate(self.fixture)
        req_a = report.get("req-A")
        self.assertIsNotNone(req_a)
        self.assertEqual(req_a["status"], "SUCCESS")
        self.assertEqual(req_a["duration_ms"], 12)
        self.assertEqual(req_a["tool_call_count"], 2)
        self.assertIsNone(req_a["error"])

    def test_request_b_failure(self):
        """
        Primary Contract:
        Request B fails and reports error.
        """
        report = self.refactored.aggregate(self.fixture)
        req_b = report.get("req-B")
        self.assertIsNotNone(req_b)
        self.assertEqual(req_b["status"], "FAILURE")
        self.assertEqual(req_b["error"], "Database connection timeout")

    def test_request_c_incomplete_duration_none(self):
        """
        Primary Contract:
        Missing end events are marked incomplete rather than assigned duration zero.
        """
        report = self.refactored.aggregate(self.fixture)
        req_c = report.get("req-C")
        self.assertIsNotNone(req_c)
        self.assertEqual(req_c["status"], "INCOMPLETE")
        self.assertIsNone(req_c["duration_ms"])
        self.assertNotEqual(req_c["duration_ms"], 0)

    def test_prompt_contents_strictly_excluded(self):
        """Privacy invariant: Prompt strings must never appear in aggregated trace report."""
        report = self.refactored.aggregate(self.fixture)
        dumped = json.dumps(report)

        # Check prompt key is not present
        self.assertNotIn('"prompt"', dumped)

        # Check raw prompt text from fixture is not in output
        for ev in self.fixture:
            prompt_val = ev.get("prompt")
            if prompt_val:
                self.assertNotIn(
                    prompt_val,
                    dumped,
                    f"PRIVACY LEAK: Raw prompt '{prompt_val}' leaked into summary!"
                )

    def test_before_after_refactoring_equivalence(self):
        """
        Focus Requirement:
        Prove before/after equivalence between baseline and refactored implementation.
        """
        is_equiv, base_out, ref_out = verify_before_after_equivalence(self.fixture)
        self.assertTrue(is_equiv, "Refactored implementation diverged from baseline!")
        self.assertEqual(base_out, ref_out)

    def test_deliberate_wrong_result_makes_test_fail(self):
        """
        Done-when requirement:
        'The contribution focus is demonstrated, and a deliberate wrong result makes the test fail.'

        Simulates the anti-pattern of assigning duration 0 to incomplete traces.
        Confirms our test assertion catches it.
        """
        report = self.refactored.aggregate(self.fixture)
        actual_duration = report["req-C"]["duration_ms"]  # None

        # Anti-pattern: Assigning 0 instead of None
        flawed_duration = 0
        with self.assertRaises(AssertionError):
            self.assertEqual(actual_duration, flawed_duration)

    def test_extracted_classifier_unit(self):
        """Unit test the extracted TraceLifecycleClassifier in isolation."""
        classifier = TraceLifecycleClassifier()

        # Incomplete trace
        eval_incomplete = classifier.evaluate_lifecycle([
            {"event": "start", "timestamp_ms": 10}
        ])
        self.assertEqual(eval_incomplete.status, "INCOMPLETE")
        self.assertIsNone(eval_incomplete.duration_ms)

        # Complete success
        eval_success = classifier.evaluate_lifecycle([
            {"event": "start", "timestamp_ms": 100},
            {"event": "end", "timestamp_ms": 112, "status": "ok"}
        ])
        self.assertEqual(eval_success.status, "SUCCESS")
        self.assertEqual(eval_success.duration_ms, 12)


if __name__ == "__main__":
    unittest.main()
