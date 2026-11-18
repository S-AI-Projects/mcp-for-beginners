"""Unit tests for R49-T019 configuration validation evaluation experiment."""

import unittest

from example import evaluate_sizes, generate_fixture, validate_launch_config


class TestLaunchConfigEvaluation(unittest.TestCase):
    """Test suite evaluating controlled input sizes and validation boundaries."""

    def test_evaluate_three_sizes(self):
        """Evaluation across small, medium, and large configurations reports 100% correctness."""
        metrics = evaluate_sizes()
        self.assertEqual(len(metrics), 3)
        for m in metrics:
            self.assertTrue(m["correct"])
            self.assertEqual(m["command"], "python")

    def test_values_are_redacted_across_sizes(self):
        """Values in env dictionaries are never exposed in output summaries."""
        for sz in ["small", "medium", "large"]:
            fixture = generate_fixture(sz)
            res = validate_launch_config(fixture)
            for v in fixture["env"].values():
                self.assertNotIn(v, str(res))

    def test_missing_command_raises_value_error(self):
        """Missing command fails validation."""
        with self.assertRaises(ValueError):
            validate_launch_config({"args": ["server.py"]})

    def test_empty_command_raises_value_error(self):
        """Empty or whitespace command fails validation."""
        with self.assertRaises(ValueError):
            validate_launch_config({"command": "  ", "args": []})

    def test_string_arguments_fail_validation(self):
        """String arguments instead of list raise ValueError."""
        with self.assertRaises(ValueError):
            validate_launch_config({"command": "node", "args": "server.js"})

    def test_empty_arguments_boundary(self):
        """Empty arguments list is valid."""
        res = validate_launch_config({"command": "python", "args": []})
        self.assertEqual(res["args"], [])
        self.assertEqual(res["environment_keys"], [])


if __name__ == "__main__":
    unittest.main()
