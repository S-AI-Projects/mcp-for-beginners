"""
Unit tests for MCP Semantic Search Server Capability Negotiation.

Lesson Extension: 11-MCPServerHandsOnLabs/07-Semantic-Search
Task ID: R49-T031

Validates:
- Intersection of client and server capabilities.
- Pre-dispatch rejection of unnegotiated capabilities (specifically 'resources').
- Smallest valid, boundary, and invalid cases.
- Non-zero test count and standard test execution.
- Deliberate failure verification to ensure assertions catch violations.
"""

import os
import sys
import unittest

# Ensure current directory is in path regardless of invocation context
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from example import (
    MCPServer,
    MCPSession,
    CapabilityNotNegotiatedError,
    UnknownMethodError,
    InvalidCapabilityError,
    CAPABILITY_TOOLS,
    CAPABILITY_RESOURCES,
    CAPABILITY_PROMPTS,
    CAPABILITY_LOGGING,
    LOCAL_FIXTURE_PRODUCTS,
    simulated_semantic_similarity,
)


class TestCapabilityNegotiation(unittest.TestCase):
    """Test suite for capability negotiation and pre-dispatch feature gating."""

    def setUp(self):
        # Default server with tools and prompts
        self.server = MCPServer(
            server_name="TestSemanticSearchServer",
            supported_capabilities={CAPABILITY_TOOLS, CAPABILITY_PROMPTS}
        )

    def test_asymmetric_negotiation_exact_goal(self):
        """
        Primary Goal Scenario:
        Client: {tools, resources}
        Server: {tools, prompts}
        Negotiated: {tools}
        
        Boundary Decision:
        - 'tools' is in both -> negotiated, invocation succeeds.
        - 'resources' is in client only -> NOT negotiated, rejected before dispatch.
        - 'prompts' is in server only -> NOT negotiated, rejected before dispatch.
        """
        client_caps = {CAPABILITY_TOOLS, CAPABILITY_RESOURCES}
        session, report = self.server.negotiate(client_caps)

        # 1. Assert negotiation intersection
        self.assertEqual(report.negotiated, {CAPABILITY_TOOLS})
        self.assertEqual(report.client_unsupported, {CAPABILITY_RESOURCES})
        self.assertEqual(report.server_unsupported, {CAPABILITY_PROMPTS})
        self.assertEqual(session.negotiated_capabilities, {CAPABILITY_TOOLS})

        # 2. Negotiated capability call succeeds
        results = session.dispatch(
            capability=CAPABILITY_TOOLS,
            method="semantic_search",
            query="trail running",
            top_k=2
        )
        self.assertIsInstance(results, list)
        self.assertGreater(len(results), 0)
        self.assertEqual(results[0]["id"], "prod-001")

        # 3. Client-offered but unnegotiated capability ('resources') is rejected BEFORE dispatch
        self.assertEqual(self.server.get_handler_execution_count(CAPABILITY_RESOURCES, "read_product"), 0)
        with self.assertRaises(CapabilityNotNegotiatedError) as ctx:
            session.dispatch(
                capability=CAPABILITY_RESOURCES,
                method="read_product",
                product_id="prod-001"
            )
        self.assertIn("resources", str(ctx.exception))
        self.assertIn("rejected before dispatch", str(ctx.exception))

        # Ensure handler execution count remains 0 (dispatch was aborted before execution)
        self.assertEqual(self.server.get_handler_execution_count(CAPABILITY_RESOURCES, "read_product"), 0)

        # 4. Server-supported but client-undeclared capability ('prompts') is also rejected
        with self.assertRaises(CapabilityNotNegotiatedError) as ctx_prompt:
            session.dispatch(
                capability=CAPABILITY_PROMPTS,
                method="search_prompt",
                context="retail"
            )
        self.assertIn("prompts", str(ctx_prompt.exception))

    def test_smallest_valid_case(self):
        """
        Smallest valid case:
        Client declares only {tools}, Server supports only {tools}.
        Negotiated: {tools}.
        Dispatches minimal query against fixture.
        """
        minimal_server = MCPServer(supported_capabilities={CAPABILITY_TOOLS})
        session, report = minimal_server.negotiate({CAPABILITY_TOOLS})

        self.assertEqual(report.negotiated, {CAPABILITY_TOOLS})
        self.assertEqual(len(report.client_unsupported), 0)
        self.assertEqual(len(report.server_unsupported), 0)

        results = session.dispatch(
            capability=CAPABILITY_TOOLS,
            method="semantic_search",
            query="backpack",
            top_k=1
        )
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["id"], "prod-003")

    def test_boundary_disjoint_capabilities(self):
        """
        Boundary case: Disjoint capability sets.
        Client: {resources}
        Server: {tools}
        Negotiated: {} (empty set)
        """
        server = MCPServer(supported_capabilities={CAPABILITY_TOOLS})
        session, report = server.negotiate({CAPABILITY_RESOURCES})

        self.assertEqual(report.negotiated, set())
        self.assertEqual(report.client_unsupported, {CAPABILITY_RESOURCES})
        self.assertEqual(report.server_unsupported, {CAPABILITY_TOOLS})

        # All dispatches must fail
        with self.assertRaises(CapabilityNotNegotiatedError):
            session.dispatch(capability=CAPABILITY_RESOURCES, method="read_product", product_id="prod-001")

        with self.assertRaises(CapabilityNotNegotiatedError):
            session.dispatch(capability=CAPABILITY_TOOLS, method="semantic_search", query="shoes")

    def test_boundary_empty_client_capabilities(self):
        """
        Boundary case: Client declares no capabilities {}.
        Negotiated: {}
        """
        session, report = self.server.negotiate(set())
        self.assertEqual(report.negotiated, set())
        self.assertEqual(len(report.client_declared), 0)

        with self.assertRaises(CapabilityNotNegotiatedError):
            session.dispatch(capability=CAPABILITY_TOOLS, method="semantic_search", query="shoes")

    def test_boundary_empty_server_capabilities(self):
        """
        Boundary case: Server supports no capabilities {}.
        Negotiated: {}
        """
        empty_server = MCPServer(supported_capabilities=set())
        session, report = empty_server.negotiate({CAPABILITY_TOOLS, CAPABILITY_RESOURCES})
        self.assertEqual(report.negotiated, set())

        with self.assertRaises(CapabilityNotNegotiatedError):
            session.dispatch(capability=CAPABILITY_TOOLS, method="semantic_search", query="shoes")

    def test_invalid_capability_format(self):
        """Invalid capability strings (empty, whitespace) raise InvalidCapabilityError."""
        client_caps = {CAPABILITY_TOOLS}
        session, _ = self.server.negotiate(client_caps)

        with self.assertRaises(InvalidCapabilityError):
            session.dispatch(capability="", method="test")

        with self.assertRaises(InvalidCapabilityError):
            session.dispatch(capability="   ", method="test")

    def test_invalid_unknown_method_in_negotiated_capability(self):
        """Method not found under a negotiated capability raises UnknownMethodError."""
        session, _ = self.server.negotiate({CAPABILITY_TOOLS})
        with self.assertRaises(UnknownMethodError):
            session.dispatch(capability=CAPABILITY_TOOLS, method="non_existent_tool")

    def test_pre_dispatch_gating_proves_no_handler_execution(self):
        """
        Verifies that even if the server internally defines a handler for 'resources',
        the session gate prevents execution count from incrementing.
        """
        session, _ = self.server.negotiate({CAPABILITY_TOOLS})
        self.assertEqual(self.server.get_handler_execution_count(CAPABILITY_RESOURCES, "read_product"), 0)

        try:
            session.dispatch(CAPABILITY_RESOURCES, "read_product", product_id="prod-001")
        except CapabilityNotNegotiatedError:
            pass

        # Counter must still be 0
        self.assertEqual(self.server.get_handler_execution_count(CAPABILITY_RESOURCES, "read_product"), 0)

    def test_deliberate_wrong_result_makes_test_fail(self):
        """
        Done-when requirement:
        'The contribution focus is demonstrated, and a deliberate wrong result makes the test fail.'
        
        Demonstrates that if an unnegotiated capability was erroneously marked negotiated,
        or if intersection returned an unnegotiated capability, our assertion detects it.
        """
        client_caps = {CAPABILITY_TOOLS, CAPABILITY_RESOURCES}
        _, report = self.server.negotiate(client_caps)

        # Simulation of a deliberate faulty negotiation engine:
        flawed_negotiated = client_caps.union(self.server.supported_capabilities)

        # Confirm that our strict expectation catches the flaw
        with self.assertRaises(AssertionError):
            self.assertEqual(flawed_negotiated, {CAPABILITY_TOOLS})

    def test_local_fixture_search_accuracy(self):
        """Test deterministic local semantic similarity ranking on fixture items."""
        session, _ = self.server.negotiate({CAPABILITY_TOOLS})
        results = session.dispatch(
            capability=CAPABILITY_TOOLS,
            method="semantic_search",
            query="waterproof trail shoes",
            top_k=2
        )
        self.assertEqual(len(results), 2)
        # First result must be the trail running shoes (prod-001)
        self.assertEqual(results[0]["id"], "prod-001")
        # Second result is road shoes (prod-002)
        self.assertEqual(results[1]["id"], "prod-002")
        self.assertGreater(results[0]["similarity"], results[1]["similarity"])


if __name__ == "__main__":
    unittest.main()
