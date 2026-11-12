"""Tests for the local mock configuration validator."""

import unittest

from example import validate_config


class TestValidateConfig(unittest.TestCase):

    def test_valid_configuration(self):
        config = {
            "command": "python",
            "args": ["server.py"],
            "env": {"API_KEY": "secret123"},
        }

        result = validate_config(config)

        self.assertEqual(result["command"], "python")
        self.assertEqual(result["args"], ["server.py"])
        self.assertEqual(result["environment_keys"], ["API_KEY"])
        self.assertNotIn("secret123", str(result))

    def test_missing_command_fails(self):
        config = {"args": ["server.py"], "env": {}}

        with self.assertRaises(ValueError):
            validate_config(config)

    def test_empty_command_fails(self):
        config = {"command": " ", "args": [], "env": {}}

        with self.assertRaises(ValueError):
            validate_config(config)

    def test_string_arguments_fail(self):
        config = {
            "command": "python",
            "args": "server.py",
            "env": {},
        }

        with self.assertRaises(ValueError):
            validate_config(config)

    def test_empty_arguments_are_valid(self):
        config = {"command": "python", "args": [], "env": {}}

        result = validate_config(config)

        self.assertEqual(result["args"], [])

    def test_environment_values_are_redacted(self):
        config = {
            "command": "python",
            "args": ["server.py"],
            "env": {
                "API_KEY": "my-secret-value",
                "PORT": "8080",
            },
        }

        result = validate_config(config)

        self.assertEqual(
            result["environment_keys"],
            ["API_KEY", "PORT"],
        )
        self.assertNotIn("my-secret-value", str(result))
        self.assertNotIn("8080", str(result))

    def test_invalid_argument_item_fails(self):
        config = {
            "command": "python",
            "args": ["server.py", 8080],
            "env": {},
        }

        with self.assertRaises(ValueError):
            validate_config(config)


if __name__ == "__main__":
    unittest.main()
