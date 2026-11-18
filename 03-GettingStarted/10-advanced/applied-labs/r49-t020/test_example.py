"""Unit tests for R49-T020 typed tool dispatch and scenario assessment."""

import unittest

from example import dispatch_tool, execute_applied_checks


class TestAdvancedToolDispatch(unittest.TestCase):
    """Test suite verifying add/multiply contracts, structured errors, and scenario assessment."""

    def test_add_normal_contract(self):
        """add(2, 3) returns 5."""
        res = dispatch_tool({"tool": "add", "arguments": {"a": 2, "b": 3}})
        self.assertTrue(res["success"])
        self.assertEqual(res["result"], 5)

    def test_multiply_normal_contract(self):
        """multiply(2, 3) returns 6."""
        res = dispatch_tool({"tool": "multiply", "arguments": {"a": 2, "b": 3}})
        self.assertTrue(res["success"])
        self.assertEqual(res["result"], 6)

    def test_unknown_tool_returns_structured_error(self):
        """Unknown tool returns structured error without running fallback."""
        res = dispatch_tool({"tool": "divide", "arguments": {"a": 4, "b": 2}})
        self.assertFalse(res["success"])
        self.assertEqual(res["error"]["code"], "UNKNOWN_TOOL")

    def test_string_a_returns_structured_error(self):
        """String 'a' returns structured error without running fallback."""
        res = dispatch_tool({"tool": "add", "arguments": {"a": "2", "b": 3}})
        self.assertFalse(res["success"])
        self.assertEqual(res["error"]["code"], "INVALID_ARGUMENT_TYPE")

    def test_applied_scenario_checks_all_verified(self):
        """All three applied assessment checks (predict, diagnose, policy) verify successfully."""
        checks = execute_applied_checks()
        self.assertEqual(len(checks), 3)
        for c in checks:
            self.assertTrue(c["verified"], f"Check failed: {c['q_id']}")


if __name__ == "__main__":
    unittest.main()
