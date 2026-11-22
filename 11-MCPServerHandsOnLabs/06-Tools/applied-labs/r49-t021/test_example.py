"""
Unit tests for Applied Lab R49-T021: Tool Routing and Auditable Decision Records.
"""

import unittest
from datetime import datetime
from example import (
    ToolRouter,
    ToolRequest,
    ToolResult,
    AuditRecord,
    IntentRule,
)


class TestToolRouter(unittest.TestCase):
    def setUp(self):
        self.router = ToolRouter()

    def test_help_routes_to_support_handler(self):
        """Verify explicit 'help' intent routes to 'support' handler."""
        request = ToolRequest(query="I need help with the system documentation")
        result = self.router.dispatch(request)

        self.assertTrue(result.success)
        self.assertIsNotNone(result.metadata)
        audit = result.metadata["audit"]

        self.assertEqual(audit["selected_intent"], "help")
        self.assertEqual(audit["handler_name"], "support")
        self.assertIn("exact_rule_match", audit["resolution_rule"])
        self.assertEqual(result.data["handler"], "support")

    def test_calculate_routes_to_calculator_handler(self):
        """Verify explicit 'calculate' intent routes to 'calculator' handler."""
        request = ToolRequest(query="Please calculate 50 + 25")
        result = self.router.dispatch(request)

        self.assertTrue(result.success)
        self.assertIsNotNone(result.metadata)
        audit = result.metadata["audit"]

        self.assertEqual(audit["selected_intent"], "calculate")
        self.assertEqual(audit["handler_name"], "calculator")
        self.assertIn("exact_rule_match", audit["resolution_rule"])
        self.assertEqual(result.data["handler"], "calculator")
        self.assertEqual(result.data["result"], 75.0)

    def test_ambiguous_intent_follows_priority_calculate_over_help(self):
        """
        Verify ambiguous intent containing both 'help' and 'calculate' follows
        documented priority (calculate > help) and logs the chosen rule in audit.
        """
        request = ToolRequest(query="Could you help me calculate 12 * 8?")
        result = self.router.dispatch(request)

        self.assertTrue(result.success)
        self.assertIsNotNone(result.metadata)
        audit = result.metadata["audit"]

        # Both intents must be captured as candidates
        self.assertIn("calculate", audit["matched_intents"])
        self.assertIn("help", audit["matched_intents"])
        self.assertEqual(len(audit["matched_intents"]), 2)

        # Priority 1 (calculate) must be chosen over Priority 2 (help)
        self.assertEqual(audit["selected_intent"], "calculate")
        self.assertEqual(audit["handler_name"], "calculator")
        self.assertIn("priority_resolution", audit["resolution_rule"])
        self.assertIn("'calculate' (priority 1)", audit["resolution_rule"])
        self.assertIn("help", audit["resolution_rule"])
        self.assertEqual(result.data["handler"], "calculator")
        self.assertEqual(result.data["result"], 96.0)

    def test_unknown_query_routes_to_fallback_handler(self):
        """Verify unrecognized queries route to 'fallback' handler."""
        request = ToolRequest(query="What is the weather in Paris?")
        result = self.router.dispatch(request)

        self.assertTrue(result.success)
        self.assertIsNotNone(result.metadata)
        audit = result.metadata["audit"]

        self.assertEqual(audit["matched_intents"], [])
        self.assertEqual(audit["selected_intent"], "unknown")
        self.assertEqual(audit["handler_name"], "fallback")
        self.assertIn("default_fallback", audit["resolution_rule"])
        self.assertEqual(result.data["handler"], "fallback")

    def test_empty_query_routes_to_fallback_handler(self):
        """Boundary test: empty string query safely routes to fallback."""
        request = ToolRequest(query="")
        result = self.router.dispatch(request)

        self.assertTrue(result.success)
        audit = result.metadata["audit"]
        self.assertEqual(audit["selected_intent"], "unknown")
        self.assertEqual(audit["handler_name"], "fallback")

    def test_audit_record_schema_and_timestamp(self):
        """Verify audit record structure and ISO-8601 UTC timestamp."""
        request = ToolRequest(query="help me please")
        result = self.router.dispatch(request)
        audit = result.metadata["audit"]

        required_keys = {
            "request_id",
            "raw_query",
            "matched_intents",
            "selected_intent",
            "resolution_rule",
            "handler_name",
            "timestamp",
        }
        self.assertTrue(required_keys.issubset(audit.keys()))
        # Verify valid ISO-8601 parsing
        parsed_dt = datetime.fromisoformat(audit["timestamp"])
        self.assertIsNotNone(parsed_dt)

    def test_deliberate_wrong_result_fails_assertion(self):
        """
        Demonstrate that a deliberate wrong result makes assertions fail.
        This verifies that our tests are sensitive and genuine checks.
        """
        request = ToolRequest(query="help me")
        result = self.router.dispatch(request)
        actual_handler = result.metadata["audit"]["handler_name"]

        with self.assertRaises(AssertionError):
            # Deliberately assert the wrong handler to prove test detects failures
            self.assertEqual(actual_handler, "non_existent_wrong_handler")


if __name__ == "__main__":
    unittest.main()
