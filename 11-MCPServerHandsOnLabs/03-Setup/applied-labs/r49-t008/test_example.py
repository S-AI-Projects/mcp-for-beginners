import json
import unittest
from unittest.mock import patch

import example


class TestTypedToolDispatch(unittest.TestCase):

    def test_add(self):
        result = example.dispatch_json(
            '{"tool":"add","arguments":{"a":2,"b":3}}'
        )
        self.assertEqual(result["result"], 5)
        self.assertTrue(result["ok"])

    def test_multiply(self):
        result = example.dispatch_json(
            '{"tool":"multiply","arguments":{"a":2,"b":3}}'
        )
        self.assertEqual(result["result"], 6)
        self.assertTrue(result["ok"])

    def test_unknown_tool_returns_structured_error(self):
        result = example.dispatch_json(
            '{"tool":"divide","arguments":{"a":2,"b":3}}'
        )
        self.assertFalse(result["ok"])
        self.assertEqual(result["error"]["code"], "UNKNOWN_TOOL")

    def test_string_argument_returns_structured_error(self):
        result = example.dispatch_json(
            '{"tool":"add","arguments":{"a":"2","b":3}}'
        )
        self.assertFalse(result["ok"])
        self.assertEqual(result["error"]["code"], "INVALID_ARGUMENT")

    def test_failed_call_does_not_execute_any_tool(self):
        add_spy = unittest.mock.Mock(return_value=5)
        multiply_spy = unittest.mock.Mock(return_value=6)

        with patch.dict(
            example.TOOLS,
            {"add": add_spy, "multiply": multiply_spy},
        ):
            result = example.dispatch_json(
                '{"tool":"add","arguments":{"a":"2","b":3}}'
            )

            self.assertFalse(result["ok"])
            add_spy.assert_not_called()
            multiply_spy.assert_not_called()

    def test_valid_call_recovers_after_failure(self):
        failed = example.dispatch_json(
            '{"tool":"divide","arguments":{"a":2,"b":3}}'
        )
        recovered = example.dispatch_json(
            '{"tool":"add","arguments":{"a":2,"b":3}}'
        )

        self.assertFalse(failed["ok"])
        self.assertEqual(recovered["result"], 5)

    def test_missing_argument(self):
        result = example.dispatch_json(
            '{"tool":"add","arguments":{"a":2}}'
        )
        self.assertEqual(result["error"]["code"], "INVALID_ARGUMENTS")

    def test_invalid_json(self):
        result = example.dispatch_json('{"tool":')
        self.assertEqual(result["error"]["code"], "INVALID_JSON")

    def test_boolean_is_not_a_number(self):
        result = example.dispatch_json(
            '{"tool":"add","arguments":{"a":true,"b":3}}'
        )
        self.assertEqual(result["error"]["code"], "INVALID_ARGUMENT")

if __name__ == "__main__":
    unittest.main()
