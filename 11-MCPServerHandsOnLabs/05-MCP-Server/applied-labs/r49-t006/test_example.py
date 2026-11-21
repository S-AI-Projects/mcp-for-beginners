
import unittest
import math
from unittest.mock import patch

from example import TOOL_ALLOWLIST, dispatch


def baseline_dispatch(tool_name, arguments):
    """Original inline-validation baseline."""

    if not isinstance(tool_name, str) or tool_name not in TOOL_ALLOWLIST:
        return {
            "ok": False,
            "error": {
                "code": "unknown_tool",
                "message": "Tool is not in the allowlist.",
            },
        }

    valid = (
        isinstance(arguments, dict)
        and set(arguments) == {"a", "b"}
        and all(
            not isinstance(value, bool)
            and isinstance(value, (int, float))
            and math.isfinite(value)
            for value in arguments.values()
        )
    )

    if not valid:
        return {
            "ok": False,
            "error": {
                "code": "invalid_arguments",
                "message": "Expected numeric arguments 'a' and 'b'.",
            },
        }

    return {
        "ok": True,
        "result": TOOL_ALLOWLIST[tool_name](
            arguments["a"], arguments["b"]
        ),
    }


class TestTypedToolDispatch(unittest.TestCase):

    def test_add(self):
        self.assertEqual(
            dispatch("add", {"a": 2, "b": 3}),
            {"ok": True, "result": 5}
        )

    def test_multiply(self):
        self.assertEqual(
            dispatch("multiply", {"a": 2, "b": 3}),
            {"ok": True, "result": 6}
        )

    def test_unknown_tool(self):
        result = dispatch("divide", {"a": 2, "b": 3})
        self.assertFalse(result["ok"])
        self.assertEqual(result["error"]["code"], "unknown_tool")

    def test_string_argument(self):
        result = dispatch("add", {"a": "2", "b": 3})
        self.assertFalse(result["ok"])
        self.assertEqual(result["error"]["code"], "invalid_arguments")

    def test_boolean_argument(self):
        result = dispatch("add", {"a": True, "b": 3})
        self.assertFalse(result["ok"])

    def test_missing_argument(self):
        result = dispatch("add", {"a": 2})
        self.assertFalse(result["ok"])

    def test_failed_call_does_not_execute_another_tool(self):
        with patch.dict(TOOL_ALLOWLIST) as tools:
            spy = unittest.mock.Mock()
            tools["add"] = spy

            result = dispatch("unknown", {"a": 2, "b": 3})

            self.assertFalse(result["ok"])
            spy.assert_not_called()

    def test_before_after_equivalence(self):
        fixtures = [
            ("add", {"a": 2, "b": 3}),
            ("multiply", {"a": 2, "b": 3}),
            ("unknown", {"a": 2, "b": 3}),
            ("add", {"a": "2", "b": 3}),
            ("add", {"a": True, "b": 3}),
            ("add", {"a": 2}),
        ]

        for tool, arguments in fixtures:
            with self.subTest(tool=tool, arguments=arguments):
                self.assertEqual(
                    baseline_dispatch(tool, arguments),
                    dispatch(tool, arguments),
                )
    def test_extra_argument(self):
        result = dispatch("add", {"a": 2, "b": 3, "c": 4})
        self.assertFalse(result["ok"])

    def test_infinite_argument(self):
        result = dispatch("add", {"a": float("inf"), "b": 3})
        self.assertFalse(result["ok"])
      
if __name__ == "__main__":
    unittest.main()
