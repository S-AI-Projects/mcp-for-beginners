"""
Unit and Contract Tests for Advanced Topics Runnable Concept Example (R49-T040).
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from example import (
    AdvancedTopicsToolDispatcher,
    METHOD_NOT_FOUND,
    INVALID_PARAMS,
    LESSON_CONCEPT_MAPPINGS,
)


class TestAdvancedTopicsToolDispatcher(unittest.TestCase):
    """Test suite verifying contract execution, error envelopes, and concept mappings."""

    def setUp(self):
        self.dispatcher = AdvancedTopicsToolDispatcher()

    def test_add_operation_valid(self):
        """Contract: add(2,3) -> 5."""
        req = {"jsonrpc": "2.0", "id": 1, "tool": "add", "params": {"a": 2, "b": 3}}
        resp = self.dispatcher.dispatch(req)
        self.assertEqual(resp.get("id"), 1)
        self.assertNotIn("error", resp)
        self.assertEqual(resp.get("result", {}).get("value"), 5)
        self.assertEqual(self.dispatcher.get_tool_call_count("add"), 1)

    def test_multiply_operation_valid(self):
        """Contract: multiply(2,3) -> 6."""
        req = {"jsonrpc": "2.0", "id": 2, "tool": "multiply", "params": {"a": 2, "b": 3}}
        resp = self.dispatcher.dispatch(req)
        self.assertEqual(resp.get("id"), 2)
        self.assertNotIn("error", resp)
        self.assertEqual(resp.get("result", {}).get("value"), 6)
        self.assertEqual(self.dispatcher.get_tool_call_count("multiply"), 1)

    def test_unknown_tool_structured_error(self):
        """Contract: unknown tool yields structured error (-32601)."""
        req = {"jsonrpc": "2.0", "id": 3, "tool": "unauthorized_tool", "params": {"a": 1, "b": 1}}
        resp = self.dispatcher.dispatch(req)
        self.assertEqual(resp.get("id"), 3)
        self.assertIn("error", resp)
        self.assertEqual(resp["error"]["code"], METHOD_NOT_FOUND)
        self.assertIn("not allowlisted", resp["error"]["message"])

    def test_string_parameter_structured_error(self):
        """Contract: string 'a' yields structured error (-32602)."""
        req = {"jsonrpc": "2.0", "id": 4, "tool": "add", "params": {"a": "2", "b": 3}}
        resp = self.dispatcher.dispatch(req)
        self.assertEqual(resp.get("id"), 4)
        self.assertIn("error", resp)
        self.assertEqual(resp["error"]["code"], INVALID_PARAMS)
        self.assertIn("must be numeric", resp["error"]["message"])

    def test_circuit_isolation(self):
        """Contract: a failed call cannot execute another tool (zero side effects)."""
        req_bad1 = {"jsonrpc": "2.0", "id": 5, "tool": "unknown_tool", "params": {"a": 1, "b": 1}}
        self.dispatcher.dispatch(req_bad1)

        req_bad2 = {"jsonrpc": "2.0", "id": 6, "tool": "multiply", "params": {"a": "bad", "b": 2}}
        self.dispatcher.dispatch(req_bad2)

        self.assertEqual(self.dispatcher.get_tool_call_count("add"), 0)
        self.assertEqual(self.dispatcher.get_tool_call_count("multiply"), 0)
        self.assertEqual(sum(self.dispatcher.execution_counts.values()), 0)

    def test_lesson_concept_mappings_completeness(self):
        """Focus: verify each public input and output connects to an advanced lesson concept."""
        self.assertGreaterEqual(len(LESSON_CONCEPT_MAPPINGS), 5)
        for mapping in LESSON_CONCEPT_MAPPINGS:
            self.assertTrue(mapping.input_or_output)
            self.assertTrue(mapping.lesson_concept)
            self.assertTrue(mapping.architectural_rationale)

    def test_deliberate_wrong_result_makes_test_fail(self):
        """Ensure test harness detects incorrect behavior (prevent silent false positives)."""
        req = {"jsonrpc": "2.0", "id": 99, "tool": "add", "params": {"a": 2, "b": 3}}
        resp = self.dispatcher.dispatch(req)
        with self.assertRaises(AssertionError):
            self.assertEqual(resp.get("result", {}).get("value"), 999)


if __name__ == "__main__":
    unittest.main()
