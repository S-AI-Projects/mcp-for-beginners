
import unittest

from example import ConsentGate


class TestConsentGate(unittest.TestCase):

    def test_initial_state(self):
        gate = ConsentGate()

        self.assertEqual(gate.state, "pending")
        self.assertEqual(gate.model_call_count, 0)
        self.assertIsNone(gate.result)

    def test_approved_consent(self):
        gate = ConsentGate()

        gate.decide("approved")

        self.assertEqual(gate.state, "approved")
        self.assertEqual(gate.model_call_count, 1)
        self.assertEqual(gate.result, "Mock model response")

    def test_denied_consent(self):
        gate = ConsentGate()

        gate.decide("denied")

        self.assertEqual(gate.state, "denied")
        self.assertEqual(gate.model_call_count, 0)
        self.assertIsNone(gate.result)

    def test_duplicate_approval(self):
        gate = ConsentGate()

        gate.decide("approved")

        with self.assertRaises(ValueError):
            gate.decide("approved")

        self.assertEqual(gate.model_call_count, 1)

    def test_duplicate_denial(self):
        gate = ConsentGate()

        gate.decide("denied")

        with self.assertRaises(ValueError):
            gate.decide("denied")

        self.assertEqual(gate.model_call_count, 0)

    def test_invalid_decision(self):
        gate = ConsentGate()

        with self.assertRaises(ValueError):
            gate.decide("maybe")

        self.assertEqual(gate.state, "pending")
        self.assertEqual(gate.model_call_count, 0)


if __name__ == "__main__":
    unittest.main()
