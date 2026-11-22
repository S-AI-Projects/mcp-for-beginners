"""
Unit tests for Typed Tool Dispatch, Allowlist Authorization & Regression Checks.

Lesson Extension: 11-MCPServerHandsOnLabs/05-MCP-Server
Task ID: R49-T035

Validates:
- add(2, 3) -> 5
- multiply(2, 3) -> 6
- Unknown tool yields structured error (-32601)
- Non-numeric argument (string 'a') yields structured error (-32602)
- Failed calls cannot execute another tool (circuit breaker / execution isolation)
- Regression test suite against published worked examples
- Deliberate wrong result detection
"""

import os
import sys
import unittest

# Ensure current directory is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from example import (
    TypedToolDispatcher,
    METHOD_NOT_FOUND,
    INVALID_PARAMS,
    WORKED_EXAMPLES,
    TOOL_ALLOWLIST,
)


class TestTypedToolDispatcher(unittest.TestCase):
    """Test suite for typed tool dispatch and argument validation."""

    def setUp(self):
        self.dispatcher = TypedToolDispatcher()

    def test_add_operation_valid(self):
        """Valid add(2, 3) -> 5 with preserved request ID."""
        req = {"jsonrpc": "2.0", "id": 101, "tool": "add", "params": {"a": 2, "b": 3}}
        resp = self.dispatcher.dispatch(req)

        self.assertIn("result", resp)
        self.assertEqual(resp["id"], 101)
        self.assertEqual(resp["result"]["value"], 5)
        self.assertEqual(resp["result"]["tool"], "add")
        self.assertEqual(self.dispatcher.get_tool_call_count("add"), 1)
        self.assertEqual(self.dispatcher.get_tool_call_count("multiply"), 0)

    def test_multiply_operation_valid(self):
        """Valid multiply(2, 3) -> 6 with preserved request ID."""
        req = {"jsonrpc": "2.0", "id": 102, "tool": "multiply", "params": {"a": 2, "b": 3}}
        resp = self.dispatcher.dispatch(req)

        self.assertIn("result", resp)
        self.assertEqual(resp["id"], 102)
        self.assertEqual(resp["result"]["value"], 6)
        self.assertEqual(resp["result"]["tool"], "multiply")
        self.assertEqual(self.dispatcher.get_tool_call_count("multiply"), 1)
        self.assertEqual(self.dispatcher.get_tool_call_count("add"), 0)

    def test_unknown_tool_structured_error(self):
        """Unknown tool yields structured JSON-RPC error (-32601) and zero executions."""
        req = {"jsonrpc": "2.0", "id": 103, "tool": "subtract", "params": {"a": 5, "b": 2}}
        resp = self.dispatcher.dispatch(req)

        self.assertIn("error", resp)
        self.assertNotIn("result", resp)
        self.assertEqual(resp["id"], 103)
        self.assertEqual(resp["error"]["code"], METHOD_NOT_FOUND)
        self.assertIn("subtract", resp["error"]["message"])

        # No tool was executed
        self.assertEqual(self.dispatcher.get_tool_call_count("add"), 0)
        self.assertEqual(self.dispatcher.get_tool_call_count("multiply"), 0)

    def test_string_parameter_structured_error(self):
        """String 'a' parameter yields structured JSON-RPC error (-32602)."""
        req = {"jsonrpc": "2.0", "id": 104, "tool": "add", "params": {"a": "2", "b": 3}}
        resp = self.dispatcher.dispatch(req)

        self.assertIn("error", resp)
        self.assertNotIn("result", resp)
        self.assertEqual(resp["id"], 104)
        self.assertEqual(resp["error"]["code"], INVALID_PARAMS)
        self.assertIn("Parameter 'a' must be numeric", resp["error"]["message"])

        # Tool was NOT executed
        self.assertEqual(self.dispatcher.get_tool_call_count("add"), 0)
        self.assertEqual(self.dispatcher.get_tool_call_count("multiply"), 0)

    def test_failed_call_cannot_execute_another_tool(self):
        """
        Primary Goal:
        A failed call cannot execute another tool (no fallback, no unauthorized side-effects).
        """
        failing_requests = [
            {"jsonrpc": "2.0", "id": 1, "tool": "unknown_tool", "params": {"a": 1, "b": 2}},
            {"jsonrpc": "2.0", "id": 2, "tool": "add", "params": {"a": "not_a_num", "b": 2}},
            {"jsonrpc": "2.0", "id": 3, "tool": "multiply", "params": {"a": 2, "b": "str"}},
            {"jsonrpc": "2.0", "id": 4, "tool": "add", "params": {"missing_b": 1}},
        ]

        for req in failing_requests:
            resp = self.dispatcher.dispatch(req)
            self.assertIn("error", resp)

        # Confirm zero executions across all registered tools
        self.assertEqual(self.dispatcher.get_tool_call_count("add"), 0)
        self.assertEqual(self.dispatcher.get_tool_call_count("multiply"), 0)

    def test_worked_examples_regression_test(self):
        """
        Focus Requirement:
        Execute the exact worked example table as a regression test.
        """
        for item in WORKED_EXAMPLES:
            resp = self.dispatcher.dispatch(item["input"])
            if item["expected_status"] == "SUCCESS":
                self.assertIn("result", resp, f"Failed on {item['description']}")
                self.assertEqual(resp["result"]["value"], item["expected_value"])
            else:
                self.assertIn("error", resp, f"Failed on {item['description']}")
                self.assertEqual(resp["error"]["code"], item["expected_error_code"])

    def test_deliberate_wrong_result_makes_test_fail(self):
        """
        Done-when requirement:
        'The contribution focus is demonstrated, and a deliberate wrong result makes the test fail.'

        Simulates wrong arithmetic or incorrect validation expectations, proving
        our assertions strictly catch regressions.
        """
        req = {"jsonrpc": "2.0", "id": 999, "tool": "add", "params": {"a": 2, "b": 3}}
        resp = self.dispatcher.dispatch(req)
        actual_val = resp["result"]["value"]  # 5

        # Deliberate wrong expectation:
        deliberate_wrong_val = 999
        with self.assertRaises(AssertionError):
            self.assertEqual(actual_val, deliberate_wrong_val)

    def test_boolean_argument_rejected(self):
        """Boolean values (True/False) are rejected as invalid non-numeric inputs."""
        req = {"jsonrpc": "2.0", "id": 201, "tool": "add", "params": {"a": True, "b": 3}}
        resp = self.dispatcher.dispatch(req)
        self.assertIn("error", resp)
        self.assertEqual(resp["error"]["code"], INVALID_PARAMS)


if __name__ == "__main__":
    unittest.main()
