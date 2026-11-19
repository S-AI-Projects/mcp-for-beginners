import json
import unittest
from unittest.mock import Mock, patch

import example


class TestToolDispatch(unittest.TestCase):

    def test_add(self):
        request = json.dumps({
            "tool": "add",
            "arguments": {"a": 2, "b": 3},
        })
        self.assertEqual(example.dispatch(request), {"ok": True, "result": 5})

    def test_multiply(self):
        request = json.dumps({
            "tool": "multiply",
            "arguments": {"a": 2, "b": 3},
        })
        self.assertEqual(example.dispatch(request), {"ok": True, "result": 6})

    def test_comparison_with_expected_results(self):
        cases = [
            ("add", 2, 3, 5),
            ("multiply", 2, 3, 6),
            ("add", 0, 0, 0),
            ("multiply", -2, 3, -6),
            ("add", 2.5, 1.5, 4.0),
        ]

        for tool, a, b, expected in cases:
            with self.subTest(tool=tool, a=a, b=b):
                request = json.dumps({
                    "tool": tool,
                    "arguments": {"a": a, "b": b},
                })

                actual = example.dispatch(request)
                self.assertEqual(actual["result"], expected)

    def test_unknown_tool_returns_structured_error(self):
        request = json.dumps({
            "tool": "divide",
            "arguments": {"a": 6, "b": 2},
        })

        result = example.dispatch(request)

        self.assertFalse(result["ok"])
        self.assertEqual(result["error"]["code"], "unknown_tool")

    def test_string_argument_returns_structured_error(self):
        request = json.dumps({
            "tool": "add",
            "arguments": {"a": "2", "b": 3},
        })

        result = example.dispatch(request)

        self.assertFalse(result["ok"])
        self.assertEqual(result["error"]["code"], "invalid_arguments")

    def test_boolean_argument_is_rejected(self):
        request = json.dumps({
            "tool": "add",
            "arguments": {"a": True, "b": 3},
        })

        result = example.dispatch(request)

        self.assertFalse(result["ok"])

    def test_failed_call_does_not_execute_another_tool(self):
        other_tool = Mock()

        with patch.dict(example.TOOL_ALLOWLIST, {"multiply": other_tool}):
            request = json.dumps({
                "tool": "unknown",
                "arguments": {"a": 2, "b": 3},
            })

            result = example.dispatch(request)

        self.assertFalse(result["ok"])
        other_tool.assert_not_called()

    def test_missing_argument_returns_error(self):
        request = json.dumps({
            "tool": "add",
            "arguments": {"a": 2},
        })

        result = example.dispatch(request)

        self.assertFalse(result["ok"])
        self.assertEqual(result["error"]["code"], "invalid_arguments")

    def test_invalid_json_returns_error(self):
        result = example.dispatch("{invalid json")

        self.assertFalse(result["ok"])
        self.assertEqual(result["error"]["code"], "invalid_json")

    


if __name__ == "__main__":
    unittest.main()