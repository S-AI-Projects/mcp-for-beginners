"""Unit tests for R49-T016 consent gate state machine and refactoring equivalence."""

import unittest

from example import (
    BaselineConsentGate,
    ConsentState,
    InvalidStateError,
    RefactoredConsentGate,
    run_equivalence_check,
)


class TestClientConsentGate(unittest.TestCase):
    """Test suite verifying consent transitions, model invocation limits, and equivalence."""

    def test_approved_consent_calls_model_once(self):
        """Approved consent transitions to approved and calls model stub exactly once."""
        calls = []

        def mock_model(p):
            calls.append(p)
            return "Generated response"

        gate = RefactoredConsentGate(model_stub=mock_model)
        self.assertEqual(gate.state, ConsentState.PENDING)

        res = gate.decide(approved=True, prompt="Test prompt")
        self.assertEqual(res["state"], "approved")
        self.assertEqual(res["model_calls"], 1)
        self.assertEqual(res["response"], "Generated response")
        self.assertEqual(len(calls), 1)

    def test_denied_consent_never_calls_model(self):
        """Denied consent transitions to denied and never executes the model stub."""
        calls = []

        def mock_model(p):
            calls.append(p)
            return "Never"

        gate = RefactoredConsentGate(model_stub=mock_model)
        res = gate.decide(approved=False, prompt="Test prompt")

        self.assertEqual(res["state"], "denied")
        self.assertEqual(res["model_calls"], 0)
        self.assertIsNone(res["response"])
        self.assertEqual(len(calls), 0)

    def test_completed_request_cannot_be_approved_again(self):
        """A completed request (either approved or denied) raises InvalidStateError if re-evaluated."""
        gate_app = RefactoredConsentGate()
        gate_app.decide(approved=True, prompt="Prompt 1")
        with self.assertRaises(InvalidStateError):
            gate_app.decide(approved=True, prompt="Prompt 2")

        gate_den = RefactoredConsentGate()
        gate_den.decide(approved=False, prompt="Prompt 1")
        with self.assertRaises(InvalidStateError):
            gate_den.decide(approved=True, prompt="Prompt 2")

    def test_before_after_refactoring_equivalence(self):
        """Verify before/after equivalence on standard fixtures."""
        equiv, summary = run_equivalence_check("Test equivalence")
        self.assertTrue(equiv)
        self.assertTrue(summary["reapproval_rejected"])


if __name__ == "__main__":
    unittest.main()
