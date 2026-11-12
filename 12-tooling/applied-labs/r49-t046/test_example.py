import unittest
from example import (
    validate_baseline,
    validate_configuration,
)


class ConfigurationTests(unittest.TestCase):
    def setUp(self):
        self.fixture = {
            "command": "python",
            "args": ["server.py", "--port", "8080"],
            "env": {"API_KEY": "demo-secret", "PORT": "8080"},
        }

    def test_valid_configuration(self):
        result = validate_configuration(self.fixture)
        self.assertEqual(result["command"], "python")
        self.assertEqual(result["args"], ["server.py", "--port", "8080"])
        self.assertEqual(
            result["env"],
            {"API_KEY": "[REDACTED]", "PORT": "[REDACTED]"},
        )

    def test_missing_command_fails(self):
        config = dict(self.fixture)
        config.pop("command")
        with self.assertRaises(ValueError):
            validate_configuration(config)

    def test_empty_command_fails(self):
        config = dict(self.fixture, command="")
        with self.assertRaises(ValueError):
            validate_configuration(config)

    def test_string_args_fail(self):
        config = dict(self.fixture, args="server.py")
        with self.assertRaises(ValueError):
            validate_configuration(config)

    def test_non_string_argument_fails(self):
        config = dict(self.fixture, args=["server.py", 8080])
        with self.assertRaises(ValueError):
            validate_configuration(config)

    def test_refactor_matches_baseline(self):
        self.assertEqual(
            validate_baseline(self.fixture),
            validate_configuration(self.fixture),
        )

    def test_secret_value_is_not_returned(self):
        result = validate_configuration(self.fixture)
        self.assertNotIn("demo-secret", str(result))


if __name__ == "__main__":
    unittest.main()
