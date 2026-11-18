"""Unit tests for R49-T011 capability negotiation and feature gating."""

import unittest

from example import (
    CapabilityNotNegotiatedError,
    SemanticSearchServerSession,
    negotiate_capabilities,
)


class TestCapabilityNegotiation(unittest.TestCase):
    """Test suite for capability intersection and dispatch gating."""

    def test_negotiate_contract(self):
        """Verify client {tools, resources} and server {tools, prompts} negotiates {tools}."""
        client_caps = {"tools", "resources"}
        server_caps = {"tools", "prompts"}

        negotiated = negotiate_capabilities(client_caps, server_caps)
        self.assertEqual(negotiated, {"tools"})

    def test_session_negotiate_and_dispatch_tool_success(self):
        """Negotiated 'tools' capability can be dispatched successfully."""
        session = SemanticSearchServerSession(server_capabilities={"tools", "prompts"})
        negotiated = session.negotiate({"tools", "resources"})

        self.assertEqual(negotiated, {"tools"})

        result = session.dispatch(
            capability="tools",
            method="semantic_search_products",
            query="hiking boots",
        )
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["tool"], "semantic_search_products")
        self.assertEqual(result["query"], "hiking boots")
        self.assertTrue(len(result["matches"]) > 0)

    def test_unnegotiated_capability_rejected_before_dispatch(self):
        """Calling unnegotiated 'resources' capability is rejected before dispatch."""
        session = SemanticSearchServerSession(server_capabilities={"tools", "prompts"})
        session.negotiate({"tools", "resources"})

        with self.assertRaises(CapabilityNotNegotiatedError) as ctx:
            session.dispatch(
                capability="resources",
                method="read_resource",
                uri="resource://products/catalog",
            )
        self.assertIn("resources", str(ctx.exception))
        self.assertIn("was not negotiated", str(ctx.exception))

    def test_dispatch_before_negotiation_raises_runtime_error(self):
        """Calling dispatch before negotiation is executed raises RuntimeError."""
        session = SemanticSearchServerSession(server_capabilities={"tools", "prompts"})

        with self.assertRaises(RuntimeError) as ctx:
            session.dispatch(
                capability="tools",
                method="semantic_search_products",
                query="test",
            )
        self.assertIn("not been negotiated", str(ctx.exception))

    def test_disjoint_capabilities_result_in_empty_negotiation(self):
        """When client and server capabilities are disjoint, negotiated set is empty."""
        session = SemanticSearchServerSession(server_capabilities={"tools", "prompts"})
        negotiated = session.negotiate({"logging", "sampling"})

        self.assertEqual(negotiated, set())

        with self.assertRaises(CapabilityNotNegotiatedError):
            session.dispatch("logging", "log_message", message="hello")

        with self.assertRaises(CapabilityNotNegotiatedError):
            session.dispatch("tools", "semantic_search_products", query="hello")

    def test_empty_client_capabilities(self):
        """Empty client capabilities results in empty negotiation."""
        session = SemanticSearchServerSession(server_capabilities={"tools", "prompts"})
        negotiated = session.negotiate(set())

        self.assertEqual(negotiated, set())

    def test_invalid_capability_types_raise_error(self):
        """Non-iterable, integer, or invalid string items raise TypeError or ValueError."""
        with self.assertRaises(TypeError):
            negotiate_capabilities(123, {"tools"})  # type: ignore

        with self.assertRaises(TypeError):
            negotiate_capabilities({"tools"}, None)  # type: ignore

        with self.assertRaises(ValueError):
            negotiate_capabilities([""], {"tools"})

        with self.assertRaises(ValueError):
            negotiate_capabilities({"tools"}, ["  "])

    def test_missing_handler_raises_value_error(self):
        """If a negotiated capability lacks a registered handler, ValueError is raised."""
        session = SemanticSearchServerSession(server_capabilities={"tools", "custom"})
        # Remove custom handler if any
        negotiated = session.negotiate({"custom"})
        self.assertEqual(negotiated, {"custom"})

        with self.assertRaises(ValueError) as ctx:
            session.dispatch("custom", "do_action")
        self.assertIn("No handler registered", str(ctx.exception))

    def test_custom_handler_registration(self):
        """Custom handler can be registered and invoked for a negotiated capability."""
        session = SemanticSearchServerSession(server_capabilities={"tools", "custom"})
        session.register_handler("custom", lambda method, **kwargs: f"handled_{method}")
        session.negotiate({"custom"})

        result = session.dispatch("custom", "test_method")
        self.assertEqual(result, "handled_test_method")


if __name__ == "__main__":
    unittest.main()
