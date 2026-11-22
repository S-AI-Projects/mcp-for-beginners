
import unittest

from example import validate_config, run_experiment


class TestValidateConfig(unittest.TestCase):

    def test_valid_configuration(self):
        config = {
            "command": "python3",
            "args": ["server.py", "--port", "8000"],
            "env": {"API_KEY": "secret123", "LOG_LEVEL": "INFO"},
        }

        result = validate_config(config)

        self.assertTrue(result["valid"])
        self.assertEqual(result["command"], "python3")
        self.assertEqual(result["args"], ["server.py", "--port", "8000"])
        self.assertEqual(result["environment_keys"], ["API_KEY", "LOG_LEVEL"])
        self.assertTrue(result["environment_values_redacted"])
        self.assertFalse(result["process_launched"])
        self.assertNotIn("secret123", str(result))

    def test_missing_command_fails(self):
        with self.assertRaises(ValueError):
            validate_config({"args": [], "env": {}})

    def test_empty_command_fails(self):
        with self.assertRaises(ValueError):
            validate_config({"command": "   ", "args": [], "env": {}})

    def test_string_args_fail(self):
        with self.assertRaises(ValueError):
            validate_config({
                "command": "python3",
                "args": "server.py",
                "env": {},
            })

    def test_non_string_argument_fails(self):
        with self.assertRaises(ValueError):
            validate_config({
                "command": "python3",
                "args": ["server.py", 123],
                "env": {},
            })

    def test_invalid_environment_fails(self):
        with self.assertRaises(ValueError):
            validate_config({
                "command": "python3",
                "args": [],
                "env": ["API_KEY"],
            })

    def test_non_string_environment_value_fails(self):
        with self.assertRaises(ValueError):
            validate_config({
                "command": "python3",
                "args": [],
                "env": {"API_KEY": 123},
            })

    def test_environment_values_are_not_exposed(self):
        result = validate_config({
            "command": "python3",
            "args": [],
            "env": {"TOKEN": "private-value"},
        })

        self.assertNotIn("private-value", str(result))
        self.assertIn("TOKEN", result["environment_keys"])

    def test_three_configuration_experiment(self):
        results = run_experiment()

        self.assertEqual(len(results), 3)

        for result in results:
            self.assertEqual(result["expected"], "PASS")
            self.assertEqual(result["actual"], "PASS")
            self.assertTrue(result["correct"])
            self.assertTrue(result["summary"]["environment_values_redacted"])
            self.assertFalse(result["summary"]["process_launched"])

    def test_wrong_expected_result_fails(self):
        result = run_experiment()

        result[0]["actual"] = "FAIL"

        with self.assertRaises(AssertionError):
            self.assertEqual(
                result[0]["actual"],
                result[0]["expected"]
            )

if __name__ == "__main__":
    unittest.main()
