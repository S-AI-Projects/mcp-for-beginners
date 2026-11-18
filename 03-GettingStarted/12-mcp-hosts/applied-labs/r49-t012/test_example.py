"""Unit tests for R49-T012 MCP host launch configuration validation."""

import unittest

from example import validate_launch_configuration


class TestValidateLaunchConfiguration(unittest.TestCase):
    """Test suite emphasizing smallest valid, boundary, and invalid cases."""

    def test_valid_configuration_redacts_secrets(self):
        """A valid record produces a redacted summary without exposing secret values."""
        config = {
            "command": "node",
            "args": ["build/index.js", "--port", "3000"],
            "env": {
                "AUTH_TOKEN": "secret-token-xyz",
                "PORT": "3000",
            },
        }
        result = validate_launch_configuration(config)

        self.assertEqual(result["command"], "node")
        self.assertEqual(result["args"], ["build/index.js", "--port", "3000"])
        self.assertEqual(result["environment_keys"], ["AUTH_TOKEN", "PORT"])
        self.assertNotIn("secret-token-xyz", str(result))
        self.assertNotIn("3000", result.get("environment_keys", []))

    def test_smallest_valid_configuration(self):
        """Smallest valid configuration with only command specified."""
        config = {"command": "python"}
        result = validate_launch_configuration(config)

        self.assertEqual(result["command"], "python")
        self.assertEqual(result["args"], [])
        self.assertEqual(result["environment_keys"], [])

    def test_boundary_empty_args_and_env(self):
        """Boundary case: explicitly empty argument array and empty env dictionary."""
        config = {"command": "uv", "args": [], "env": {}}
        result = validate_launch_configuration(config)

        self.assertEqual(result["command"], "uv")
        self.assertEqual(result["args"], [])
        self.assertEqual(result["environment_keys"], [])

    def test_missing_command_fails(self):
        """Missing command fails validation."""
        config = {"args": ["server.py"], "env": {}}
        with self.assertRaises(ValueError) as ctx:
            validate_launch_configuration(config)
        self.assertIn("command", str(ctx.exception))

    def test_empty_command_fails(self):
        """Empty or whitespace-only command fails validation."""
        with self.assertRaises(ValueError):
            validate_launch_configuration({"command": ""})

        with self.assertRaises(ValueError):
            validate_launch_configuration({"command": "   "})

    def test_single_string_arguments_fails(self):
        """A single string where an argument array is required fails validation."""
        config = {
            "command": "node",
            "args": "build/index.js",
            "env": {},
        }
        with self.assertRaises(ValueError) as ctx:
            validate_launch_configuration(config)
        self.assertIn("not a single string", str(ctx.exception))

    def test_non_string_in_arguments_array_fails(self):
        """Non-string items inside the arguments list fail validation."""
        config = {
            "command": "node",
            "args": ["server.js", 8080],
        }
        with self.assertRaises(ValueError) as ctx:
            validate_launch_configuration(config)
        self.assertIn("must be a string", str(ctx.exception))

    def test_invalid_environment_types_fail(self):
        """Non-dictionary env or non-string env values fail validation."""
        with self.assertRaises(ValueError):
            validate_launch_configuration({"command": "python", "env": "ENV=1"})

        with self.assertRaises(ValueError):
            validate_launch_configuration({"command": "python", "env": {"PORT": 8080}})

    def test_invalid_top_level_type_fails(self):
        """Non-dictionary input fails with TypeError."""
        with self.assertRaises(TypeError):
            validate_launch_configuration(["command", "node"])  # type: ignore


if __name__ == "__main__":
    unittest.main()
