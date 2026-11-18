"""Unit tests for R49-T015 offline service adapter and preflight checks."""

import unittest

from example import LocalOfflineAdapter, run_preflight_precheck


class TestOfflineServiceAdapterPreflight(unittest.TestCase):
    """Test suite for offline adapter preflight reporting."""

    def test_complete_fixture_passes_and_redacts(self):
        """Complete fixture passes and redacts sensitive field values."""
        adapter = LocalOfflineAdapter(
            available_executables={"node", "python3"},
            config_store={
                "host": "localhost",
                "api_key": "my-ultra-secret-key",
            },
        )
        res = run_preflight_precheck(
            adapter,
            required_executables=["node", "python3"],
            required_config_fields=["host", "api_key"],
        )
        self.assertTrue(res["passed"])
        self.assertEqual(res["failures"], [])
        self.assertEqual(res["redacted_config"]["api_key"], "[REDACTED]")
        self.assertNotIn("my-ultra-secret-key", str(res))

    def test_missing_executable_actionable_failure(self):
        """Missing executable produces distinct actionable error."""
        adapter = LocalOfflineAdapter(
            available_executables={"python3"},
            config_store={"host": "localhost"},
        )
        res = run_preflight_precheck(
            adapter,
            required_executables=["node", "python3"],
            required_config_fields=["host"],
        )
        self.assertFalse(res["passed"])
        self.assertIn("node", res["missing_executables"])
        self.assertIn("Executable missing: 'node'", res["failures"])

    def test_missing_config_field_actionable_failure(self):
        """Absent or whitespace-only config field produces distinct actionable error."""
        adapter = LocalOfflineAdapter(
            available_executables={"node"},
            config_store={"host": "   "},
        )
        res = run_preflight_precheck(
            adapter,
            required_executables=["node"],
            required_config_fields=["host", "port"],
        )
        self.assertFalse(res["passed"])
        self.assertIn("host", res["missing_config_fields"])
        self.assertIn("port", res["missing_config_fields"])

    def test_custom_secret_fields(self):
        """Custom secret fields specified by user are redacted properly."""
        adapter = LocalOfflineAdapter(
            available_executables={"python3"},
            config_store={"db_password": "p@ssword123", "host": "127.0.0.1"},
        )
        res = run_preflight_precheck(
            adapter,
            required_executables=["python3"],
            required_config_fields=["db_password", "host"],
            secret_fields={"db_password"},
        )
        self.assertTrue(res["passed"])
        self.assertEqual(res["redacted_config"]["db_password"], "[REDACTED]")
        self.assertNotIn("p@ssword123", str(res))


if __name__ == "__main__":
    unittest.main()
