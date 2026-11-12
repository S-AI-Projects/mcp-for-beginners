import unittest
from unittest.mock import Mock

from example import dispatch, compare_results, TOOLS


class TestTypedToolDispatch(unittest.TestCase):

    def test_add(self):
        self.assertEqual(dispatch("add", {"a": 2, "b": 3}), {
            "ok": True, "result": 5
        })

    def test_multiply(self):
        self.assertEqual(dispatch("multiply", {"a": 2, "b": 3}), {
            "ok": True, "result": 6
        })

    def test_unknown_tool(self):
        result = dispatch("divide", {"a": 2, "b": 3})
        self.assertFalse(result["ok"])
        self.assertEqual(result["error"]["code"], "UNKNOWN_TOOL")

    def test_string_argument_rejected(self):
        result = dispatch("add", {"a": "2", "b": 3})
        self.assertFalse(result["ok"])
        self.assertEqual(result["error"]["code"], "INVALID_ARGUMENTS")

    def test_failed_call_does_not_execute_tool(self):
        original_add = TOOLS["add"]
        mock_add = Mock()
        TOOLS["add"] = mock_add

        try:
            result = dispatch("add", {"a": "wrong", "b": 3})
            self.assertFalse(result["ok"])
            mock_add.assert_not_called()
        finally:
            TOOLS["add"] = original_add

    def test_comparison_table(self):
        results = compare_results()
        self.assertEqual(len(results), 2)
        self.assertTrue(all(item["passed"] for item in results))

    def test_wrong_expected_result_fails(self):
        result = dispatch("add", {"a": 2, "b": 3})
        with self.assertRaises(AssertionError):
            self.assertEqual(result["result"], 999)
    def test_missing_argument_rejected(self):
        result = dispatch("add", {"a": 2})
        self.assertFalse(result["ok"])
        self.assertEqual(result["error"]["code"], "INVALID_ARGUMENTS")

    def test_boolean_argument_rejected(self):
        result = dispatch("add", {"a": True, "b": 3})
        self.assertFalse(result["ok"])
        self.assertEqual(result["error"]["code"], "INVALID_ARGUMENTS")

if __name__ == "__main__":
    unittest.main()
