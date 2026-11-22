"""
Unit tests for Applied Lab R49-T025: Tool Routing with Pluggable Callable Interfaces and Adapters.
"""

import unittest
from example import (
    ToolRouter,
    ToolRequest,
    DeterministicSupportAdapter,
    DeterministicCalculatorAdapter,
    ISupportService,
    ICalculatorService,
    UNESTABLISHED_REAL_SERVICE_BEHAVIORS,
)


class CustomTestSupportAdapter:
    """Mock implementation proving interface pluggability."""
    def __init__(self):
        self.called = False

    def get_support(self, query: str):
        self.called = True
        return {"service": "CustomTestSupportAdapter", "custom_msg": "ok"}


class TestToolRouterWithAdapters(unittest.TestCase):
    def setUp(self):
        self.support_adapter = DeterministicSupportAdapter()
        self.calc_adapter = DeterministicCalculatorAdapter()
        self.router = ToolRouter(
            support_service=self.support_adapter,
            calculator_service=self.calc_adapter,
        )

    def test_help_routes_to_support_adapter(self):
        """Verify explicit 'help' intent routes to support adapter."""
        req = ToolRequest(query="I need help configuring this server")
        res = self.router.dispatch(req)

        self.assertTrue(res.success)
        audit = res.metadata["audit"]
        self.assertEqual(audit["selected_intent"], "help")
        self.assertEqual(audit["handler_name"], "support")
        self.assertEqual(self.support_adapter.invocation_count, 1)
        self.assertEqual(self.calc_adapter.invocation_count, 0)
        self.assertEqual(res.data["adapter_type"], "deterministic_local_mock")

    def test_calculate_routes_to_calculator_adapter(self):
        """Verify explicit 'calculate' intent routes to calculator adapter."""
        req = ToolRequest(query="Please calculate 40 + 60")
        res = self.router.dispatch(req)

        self.assertTrue(res.success)
        audit = res.metadata["audit"]
        self.assertEqual(audit["selected_intent"], "calculate")
        self.assertEqual(audit["handler_name"], "calculator")
        self.assertEqual(self.calc_adapter.invocation_count, 1)
        self.assertEqual(self.support_adapter.invocation_count, 0)
        self.assertEqual(res.data["result"], 100.0)

    def test_ambiguous_intent_follows_priority_calculate_over_help(self):
        """
        Verify ambiguous query matching both 'help' and 'calculate' follows
        documented priority ('calculate' > 'help') and logs the decision.
        """
        req = ToolRequest(query="Can you help me calculate 10 * 10?")
        res = self.router.dispatch(req)

        self.assertTrue(res.success)
        audit = res.metadata["audit"]
        self.assertIn("calculate", audit["matched_intents"])
        self.assertIn("help", audit["matched_intents"])
        self.assertEqual(audit["selected_intent"], "calculate")
        self.assertEqual(audit["handler_name"], "calculator")
        self.assertIn("priority_resolution", audit["resolution_rule"])

        # Isolation: calculator was called, support adapter was NOT called
        self.assertEqual(self.calc_adapter.invocation_count, 1)
        self.assertEqual(self.support_adapter.invocation_count, 0)

    def test_unknown_query_routes_to_fallback(self):
        """Verify unrecognized query routes to fallback without invoking adapters."""
        req = ToolRequest(query="Order a pizza for delivery")
        res = self.router.dispatch(req)

        self.assertTrue(res.success)
        audit = res.metadata["audit"]
        self.assertEqual(audit["selected_intent"], "unknown")
        self.assertEqual(audit["handler_name"], "fallback")
        self.assertEqual(self.support_adapter.invocation_count, 0)
        self.assertEqual(self.calc_adapter.invocation_count, 0)

    def test_empty_query_routes_to_fallback(self):
        """Boundary test: empty string safely routes to fallback."""
        req = ToolRequest(query="")
        res = self.router.dispatch(req)
        self.assertEqual(res.metadata["audit"]["handler_name"], "fallback")

    def test_pluggable_interface_injection(self):
        """Focus test: verify external dependency is behind a callable interface."""
        custom_support = CustomTestSupportAdapter()
        router = ToolRouter(support_service=custom_support)
        res = router.dispatch(ToolRequest(query="help me please"))

        self.assertTrue(res.success)
        self.assertTrue(custom_support.called)
        self.assertEqual(res.data["custom_msg"], "ok")

    def test_unestablished_real_service_behaviors_documented(self):
        """Focus test: ensure unestablished real-service behaviors are identified."""
        self.assertGreaterEqual(len(UNESTABLISHED_REAL_SERVICE_BEHAVIORS), 4)
        concatenated = " ".join(UNESTABLISHED_REAL_SERVICE_BEHAVIORS).lower()
        self.assertIn("latency", concatenated)
        self.assertIn("http", concatenated)
        self.assertIn("authentication", concatenated)

    def test_deliberate_wrong_result_fails_assertion(self):
        """Demonstrate that a deliberate wrong result makes assertions fail."""
        res = self.router.dispatch(ToolRequest(query="help"))
        with self.assertRaises(AssertionError):
            self.assertEqual(res.metadata["audit"]["handler_name"], "wrong_handler_name")


if __name__ == "__main__":
    unittest.main()
