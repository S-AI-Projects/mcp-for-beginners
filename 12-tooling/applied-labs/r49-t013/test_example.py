"""Unit tests for R49-T013 comparing direct validation with reference calculation."""

import unittest

from example import (
    BENCHMARK_CASES,
    compare_approaches,
    reference_validate_config,
    validate_server_config,
)


class TestConfigurationValidationComparison(unittest.TestCase):
    """Test suite comparing direct implementation against reference calculations."""

    def test_compare_approaches_all_agree(self):
        """All benchmark cases produce identical outcomes between direct and reference methods."""
        results = compare_approaches()
        self.assertTrue(len(results) >= 4)
        for r in results:
            self.assertTrue(r["matched"], f"Mismatch in case: {r['case_id']}")

    def test_valid_configuration_redacts_values(self):
        """Valid configuration returns sorted environment keys and hides secrets."""
        cfg = {
            "command": "python",
            "args": ["server.py"],
            "env": {"TOKEN": "super_secret_value", "PORT": "8000"},
        }
        res = validate_server_config(cfg)
        self.assertEqual(res["command"], "python")
        self.assertEqual(res["args"], ["server.py"])
        self.assertEqual(res["environment_keys"], ["PORT", "TOKEN"])
        self.assertNotIn("super_secret_value", str(res))

    def test_missing_command_raises_value_error(self):
        """Missing command fails in both direct and reference implementations."""
        cfg = {"args": ["server.py"]}
        with self.assertRaises(ValueError):
            validate_server_config(cfg)
        ok, _, reason = reference_validate_config(cfg)
        self.assertFalse(ok)

    def test_single_string_args_raises_value_error(self):
        """Single string where array is required fails in both implementations."""
        cfg = {"command": "python", "args": "server.py"}
        with self.assertRaises(ValueError):
            validate_server_config(cfg)
        ok, _, _ = reference_validate_config(cfg)
        self.assertFalse(ok)

    def test_empty_arguments_boundary(self):
        """Empty argument list is valid and returns empty list in output."""
        cfg = {"command": "uv", "args": []}
        res = validate_server_config(cfg)
        self.assertEqual(res["args"], [])

    def test_invalid_env_structure(self):
        """Non-dict environment fails validation."""
        cfg = {"command": "node", "env": ["KEY=VAL"]}
        with self.assertRaises(ValueError):
            validate_server_config(cfg)


if __name__ == "__main__":
    unittest.main()
