
import unittest
import ast
import subprocess
import sys
from pathlib import Path

from example import validate_config


class TestValidateConfig(unittest.TestCase):

    def test_valid_configuration(self):
        config = {
            "command": "python3",
            "args": ["server.py", "--port", "8000"],
            "env": {
                "API_KEY": "secret123",
                "SERVER_MODE": "development",
            },
        }

        result = validate_config(config)

        self.assertTrue(result["valid"])
        self.assertEqual(result["command"], "python3")
        self.assertEqual(result["args"], ["server.py", "--port", "8000"])
        self.assertEqual(
            result["env"],
            {
                "API_KEY": "[REDACTED]",
                "SERVER_MODE": "[REDACTED]",
            },
        )
        self.assertFalse(result["process_launched"])

    def test_missing_command(self):
        config = {"args": ["server.py"], "env": {}}

        with self.assertRaises(ValueError):
            validate_config(config)

    def test_empty_command(self):
        config = {"command": "", "args": [], "env": {}}

        with self.assertRaises(ValueError):
            validate_config(config)

    def test_arguments_as_single_string(self):
        config = {
            "command": "python3",
            "args": "server.py --port 8000",
            "env": {},
        }

        with self.assertRaises(ValueError):
            validate_config(config)

    def test_non_string_argument(self):
        config = {
            "command": "python3",
            "args": ["server.py", 8000],
            "env": {},
        }

        with self.assertRaises(ValueError):
            validate_config(config)

    def test_environment_values_are_redacted(self):
        config = {
            "command": "python3",
            "args": [],
            "env": {"API_KEY": "my-secret"},
        }

        result = validate_config(config)

        self.assertNotIn("my-secret", str(result))
        self.assertEqual(result["env"]["API_KEY"], "[REDACTED]")

    def test_invalid_environment(self):
        config = {
            "command": "python3",
            "args": [],
            "env": "API_KEY=secret",
        }

        with self.assertRaises(ValueError):
            validate_config(config)

    def test_exact_example_output(self):
        script = Path(__file__).with_name("example.py")

        result = subprocess.run(
            [sys.executable, str(script)],
            capture_output=True,
            text=True,
            check=True,
        )

        output = ast.literal_eval(result.stdout.strip())

        self.assertTrue(output["valid"])
        self.assertEqual(output["command"], "python3")
        self.assertEqual(
            output["args"],
            ["server.py", "--port", "8000"],
        )
        self.assertEqual(
            output["env"],
            {
                "API_KEY": "[REDACTED]",
                "SERVER_MODE": "[REDACTED]",
            },
        )
        self.assertFalse(output["process_launched"])


if __name__ == "__main__":
    unittest.main()
