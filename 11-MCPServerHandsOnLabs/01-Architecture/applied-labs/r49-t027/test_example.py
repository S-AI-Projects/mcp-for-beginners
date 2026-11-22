"""
Unit tests for Applied Lab R49-T027: Capability Negotiation, Gating, and Regression Test.
"""

import unittest
from example import (
    MCPSession,
    MockToolExecutor,
    MockResourceProvider,
    run_worked_explanation,
)


class TestCapabilityNegotiationAndGating(unittest.TestCase):
    def setUp(self):
        self.client_caps = {"tools", "resources"}
        self.server_caps = {"tools", "prompts"}
        self.tools = MockToolExecutor()
        self.resources = MockResourceProvider()
        self.session = MCPSession(
            client_capabilities=self.client_caps,
            server_capabilities=self.server_caps,
            tools=self.tools,
            resources=self.resources,
        )

    def test_negotiated_capabilities_intersection(self):
        """Verify client {'tools', 'resources'} ∩ server {'tools', 'prompts'} = {'tools'}."""
        self.assertEqual(self.session.negotiated_capabilities, {"tools"})

    def test_negotiated_add_succeeds(self):
        """Verify add(2, 3) -> 5 executes on negotiated tools capability."""
        req = {"capability": "tools", "target": "add", "arguments": {"a": 2, "b": 3}}
        resp = self.session.invoke(req)

        self.assertTrue(resp.success)
        self.assertEqual(resp.result, 5)
        self.assertIsNone(resp.error)
        self.assertEqual(self.tools.add_call_count, 1)

    def test_negotiated_multiply_succeeds(self):
        """Verify multiply(2, 3) -> 6 executes on negotiated tools capability."""
        req = {"capability": "tools", "target": "multiply", "arguments": {"a": 2, "b": 3}}
        resp = self.session.invoke(req)

        self.assertTrue(resp.success)
        self.assertEqual(resp.result, 6)
        self.assertIsNone(resp.error)
        self.assertEqual(self.tools.multiply_call_count, 1)

    def test_unnegotiated_resources_rejected_before_dispatch(self):
        """
        Verify calling 'resources' is rejected before dispatch when unnegotiated,
        guaranteeing the backend resource provider is never invoked.
        """
        req = {"capability": "resources", "target": "schema://sales_data"}
        resp = self.session.invoke(req)

        self.assertFalse(resp.success)
        self.assertIsNone(resp.result)
        self.assertIsNotNone(resp.error)
        self.assertEqual(resp.error.code, "UNNEGOTIATED_CAPABILITY")
        self.assertIn("was not negotiated", resp.error.message)
        # Invariant: backend provider was never called
        self.assertEqual(self.resources.call_count, 0)

    def test_unnegotiated_prompts_rejected_before_dispatch(self):
        """Verify calling 'prompts' is also rejected before dispatch."""
        req = {"capability": "prompts", "target": "summary_prompt"}
        resp = self.session.invoke(req)

        self.assertFalse(resp.success)
        self.assertEqual(resp.error.code, "UNNEGOTIATED_CAPABILITY")

    def test_invalid_tool_argument_type_rejected(self):
        """Verify invalid argument type returns structured error."""
        req = {"capability": "tools", "target": "add", "arguments": {"a": "invalid", "b": 3}}
        resp = self.session.invoke(req)

        self.assertFalse(resp.success)
        self.assertEqual(resp.error.code, "INVALID_ARGUMENT")
        self.assertEqual(self.tools.add_call_count, 0)

    def test_regression_exact_worked_example(self):
        """Focus test: Execute the exact worked input-to-output example as a regression test."""
        explanation = run_worked_explanation()

        self.assertEqual(explanation["client_capabilities"], ["resources", "tools"])
        self.assertEqual(explanation["server_capabilities"], ["prompts", "tools"])
        self.assertEqual(explanation["negotiated_capabilities"], ["tools"])
        self.assertEqual(explanation["backend_resource_provider_call_count"], 0)

        invocations = explanation["invocations"]
        self.assertEqual(len(invocations), 3)

        # Invocation 1: add(2, 3) -> 5
        self.assertEqual(invocations[0]["response"]["result"], 5)
        self.assertTrue(invocations[0]["response"]["success"])

        # Invocation 2: multiply(2, 3) -> 6
        self.assertEqual(invocations[1]["response"]["result"], 6)
        self.assertTrue(invocations[1]["response"]["success"])

        # Invocation 3: resources rejected
        self.assertFalse(invocations[2]["response"]["success"])
        self.assertEqual(invocations[2]["response"]["error"]["code"], "UNNEGOTIATED_CAPABILITY")

    def test_deliberate_wrong_result_fails_assertion(self):
        """Demonstrate that a deliberate wrong result makes assertions fail."""
        req = {"capability": "tools", "target": "add", "arguments": {"a": 2, "b": 3}}
        resp = self.session.invoke(req)
        with self.assertRaises(AssertionError):
            self.assertEqual(resp.result, 999)


if __name__ == "__main__":
    unittest.main()
