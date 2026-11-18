"""Unit tests for R49-T014 preflight checks, state trace, and invariant verification."""

import unittest

from example import PreflightChecker


class TestPreflightChecker(unittest.TestCase):
    """Test suite for read-only environment preflight checker."""

    def setUp(self):
        self.checker = PreflightChecker(
            required_executables=["node", "python3"],
            required_config_fields=["host", "port", "api_key"],
        )

    def test_complete_fixture_passes_and_verifies_invariants(self):
        """Complete fixture passes and satisfies state trace invariants."""
        res = self.checker.run_preflight(
            available_executables={"node", "python3", "npm"},
            config={"host": "127.0.0.1", "port": 3000, "api_key": "secret123"},
        )
        self.assertTrue(res["passed"])
        self.assertEqual(res["failures"], [])
        self.assertTrue(res["invariant_verified"])
        self.assertEqual(len(res["state_trace"]), 4)
        self.assertEqual(res["redacted_config"]["api_key"], "[REDACTED]")
        self.assertNotIn("secret123", str(res))

    def test_missing_executable_produces_actionable_failure(self):
        """Missing executable is captured in trace and fails the preflight."""
        res = self.checker.run_preflight(
            available_executables={"python3"},
            config={"host": "127.0.0.1", "port": 3000, "api_key": "secret123"},
        )
        self.assertFalse(res["passed"])
        self.assertEqual(res["missing_executables"], ["node"])
        self.assertIn("Missing required executable: 'node'", res["failures"])
        self.assertTrue(res["invariant_verified"])

    def test_missing_config_field_produces_actionable_failure(self):
        """Missing required configuration field fails the preflight."""
        res = self.checker.run_preflight(
            available_executables={"node", "python3"},
            config={"host": "127.0.0.1"},
        )
        self.assertFalse(res["passed"])
        self.assertIn("port", res["missing_config_fields"])
        self.assertIn("api_key", res["missing_config_fields"])
        self.assertTrue(res["invariant_verified"])

    def test_secret_values_never_printed(self):
        """Secret values are redacted and never printed in report or traces."""
        res = self.checker.run_preflight(
            available_executables={"node", "python3"},
            config={"host": "127.0.0.1", "port": 3000, "api_key": "top-secret-password-xyz"},
        )
        self.assertNotIn("top-secret-password-xyz", str(res))

    def test_multiple_failures_accumulate_correctly(self):
        """Both missing executables and missing fields accumulate with invariant preserved."""
        res = self.checker.run_preflight(
            available_executables=set(),
            config={},
        )
        self.assertFalse(res["passed"])
        self.assertEqual(len(res["missing_executables"]), 2)
        self.assertEqual(len(res["missing_config_fields"]), 3)
        self.assertEqual(len(res["failures"]), 5)
        self.assertTrue(res["invariant_verified"])


if __name__ == "__main__":
    unittest.main()
