"""
Unit tests for MCP Server Architecture: Capability Negotiation Comparison.

Lesson Extension: 11-MCPServerHandsOnLabs/01-Architecture
Task ID: R49-T032

Validates:
- Comparison between Direct Implementation (Approach 1) and Independent
  Calculation / Explicit Truth Table (Approach 2) using identical inputs.
- Client {tools, resources}, Server {tools, prompts} negotiates {tools}.
- Calling unnegotiated capability (resources) is rejected before dispatch.
- Deliberate wrong result detection.
"""

import os
import sys
import unittest

# Ensure current directory is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from example import (
    DirectMCPServer,
    DirectMCPSession,
    CapabilityNotNegotiatedError,
    UnknownMethodError,
    InvalidCapabilityError,
    CAPABILITY_TOOLS,
    CAPABILITY_RESOURCES,
    CAPABILITY_PROMPTS,
    CAPABILITY_LOGGING,
    LOCAL_FIXTURE_STORES,
    independent_capability_calculation,
    lookup_expected_table,
    compare_approaches,
    EXPLICIT_EXPECTED_TABLE,
)


class TestCapabilityNegotiationComparison(unittest.TestCase):
    """Test suite comparing Direct Implementation vs. Independent Calculation & Truth Table."""

    def setUp(self):
        self.server = DirectMCPServer(
            supported_capabilities={CAPABILITY_TOOLS, CAPABILITY_PROMPTS}
        )

    def test_primary_goal_scenario_asymmetric(self):
        """
        Primary Goal Scenario:
        Client: {tools, resources}
        Server: {tools, prompts}
        Negotiated: {tools}

        Comparison:
        - Approach 1 (Direct Implementation): yields {tools}
        - Approach 2a (Independent Calculation): yields {tools}
        - Approach 2b (Explicit Truth Table): yields {tools}
        - Calling 'tools' succeeds
        - Calling 'resources' is rejected before dispatch
        - Calling 'prompts' is rejected before dispatch
        """
        client_caps = {CAPABILITY_TOOLS, CAPABILITY_RESOURCES}
        server_caps = {CAPABILITY_TOOLS, CAPABILITY_PROMPTS}

        # 1. Approach 1: Direct Implementation
        session = self.server.negotiate(client_caps)
        direct_result = session.negotiated_capabilities

        # 2. Approach 2: Independent Calculation
        calc_result = independent_capability_calculation(client_caps, server_caps)

        # 3. Approach 2: Truth Table Lookup
        table_entry = lookup_expected_table(client_caps, server_caps)
        self.assertIsNotNone(table_entry, "Primary scenario must exist in expected truth table!")
        table_result = set(table_entry["expected_negotiated"])

        # Compare: All three approaches must yield identical sets
        self.assertEqual(direct_result, {CAPABILITY_TOOLS})
        self.assertEqual(calc_result, {CAPABILITY_TOOLS})
        self.assertEqual(table_result, {CAPABILITY_TOOLS})
        self.assertEqual(direct_result, calc_result)
        self.assertEqual(direct_result, table_result)

        # 4. Valid dispatch under negotiated capability
        metrics = session.dispatch(CAPABILITY_TOOLS, "get_store_metrics", store_id="store-101")
        self.assertEqual(metrics["city"], "Seattle")
        self.assertEqual(metrics["daily_sales"], 14250.00)

        # 5. Rejected dispatch: calling unnegotiated 'resources' rejected BEFORE dispatch
        self.assertEqual(self.server.get_call_count(CAPABILITY_RESOURCES, "read_store_schema"), 0)
        with self.assertRaises(CapabilityNotNegotiatedError) as ctx:
            session.dispatch(CAPABILITY_RESOURCES, "read_store_schema")
        self.assertIn("resources", str(ctx.exception))
        self.assertIn("rejected before dispatch", str(ctx.exception))
        self.assertEqual(self.server.get_call_count(CAPABILITY_RESOURCES, "read_store_schema"), 0)

        # 6. Rejected dispatch: server-only capability 'prompts' also rejected
        with self.assertRaises(CapabilityNotNegotiatedError) as ctx_prompt:
            session.dispatch(CAPABILITY_PROMPTS, "sales_report_prompt", region="Northwest")
        self.assertIn("prompts", str(ctx_prompt.exception))

    def test_compare_all_scenarios_in_expected_table(self):
        """
        Iterate through all canonical scenarios in EXPLICIT_EXPECTED_TABLE and verify
        that Direct Implementation matches Independent Calculation and Table expectation.
        """
        for (client_tuple, server_tuple), expected_dict in EXPLICIT_EXPECTED_TABLE.items():
            client_caps = set(client_tuple)
            server_caps = set(server_tuple)
            expected_set = set(expected_dict["expected_negotiated"])

            # Evaluate comparison helper
            record = compare_approaches(client_caps, server_caps)

            self.assertTrue(
                record.direct_matches_independent,
                f"Mismatch between Direct and Calc for inputs {client_caps} vs {server_caps}"
            )
            self.assertTrue(
                record.direct_matches_table,
                f"Mismatch between Direct and Table for inputs {client_caps} vs {server_caps}"
            )
            self.assertEqual(set(record.direct_negotiated), expected_set)
            self.assertEqual(set(record.independent_calc_negotiated), expected_set)

    def test_smallest_valid_case_comparison(self):
        """Smallest valid case: Client {tools}, Server {tools}."""
        client_caps = {CAPABILITY_TOOLS}
        server_caps = {CAPABILITY_TOOLS}

        rec = compare_approaches(client_caps, server_caps)
        self.assertEqual(rec.direct_negotiated, [CAPABILITY_TOOLS])
        self.assertEqual(rec.independent_calc_negotiated, [CAPABILITY_TOOLS])
        self.assertEqual(rec.table_expected_negotiated, [CAPABILITY_TOOLS])

    def test_disjoint_capabilities_comparison(self):
        """Boundary case: Disjoint sets Client {resources}, Server {tools}."""
        client_caps = {CAPABILITY_RESOURCES}
        server_caps = {CAPABILITY_TOOLS}

        rec = compare_approaches(client_caps, server_caps)
        self.assertEqual(rec.direct_negotiated, [])
        self.assertEqual(rec.independent_calc_negotiated, [])
        self.assertEqual(rec.table_expected_negotiated, [])

    def test_empty_client_capabilities_comparison(self):
        """Boundary case: Empty Client capabilities set."""
        client_caps = set()
        server_caps = {CAPABILITY_TOOLS, CAPABILITY_PROMPTS}

        rec = compare_approaches(client_caps, server_caps)
        self.assertEqual(rec.direct_negotiated, [])
        self.assertEqual(rec.independent_calc_negotiated, [])
        self.assertEqual(rec.table_expected_negotiated, [])

    def test_deliberate_wrong_result_makes_test_fail(self):
        """
        Done-when requirement:
        'The contribution focus is demonstrated, and a deliberate wrong result makes the test fail.'
        
        Demonstrates that if the expected truth table or independent calculation
        produces an incorrect result (e.g., claiming resources was negotiated),
        our comparative assertion catches it and fails.
        """
        client_caps = {CAPABILITY_TOOLS, CAPABILITY_RESOURCES}
        server_caps = {CAPABILITY_TOOLS, CAPABILITY_PROMPTS}

        session = self.server.negotiate(client_caps)
        actual_negotiated = session.negotiated_capabilities  # {'tools'}

        # Simulated deliberate wrong calculation / corrupted table entry:
        corrupted_expected = {CAPABILITY_TOOLS, CAPABILITY_RESOURCES}

        # Assert that comparing against deliberate wrong result fails
        with self.assertRaises(AssertionError):
            self.assertEqual(actual_negotiated, corrupted_expected)

    def test_pre_dispatch_gating_proves_zero_handler_executions(self):
        """Verify that pre-dispatch gate strictly prevents handler invocation."""
        session = self.server.negotiate({CAPABILITY_TOOLS})
        self.assertEqual(self.server.get_call_count(CAPABILITY_RESOURCES, "read_store_schema"), 0)

        try:
            session.dispatch(CAPABILITY_RESOURCES, "read_store_schema")
        except CapabilityNotNegotiatedError:
            pass

        self.assertEqual(self.server.get_call_count(CAPABILITY_RESOURCES, "read_store_schema"), 0)

    def test_invalid_capability_format(self):
        """Blank or empty capability name raises InvalidCapabilityError."""
        session = self.server.negotiate({CAPABILITY_TOOLS})
        with self.assertRaises(InvalidCapabilityError):
            session.dispatch("", "get_store_metrics")

    def test_unknown_method_in_negotiated_capability(self):
        """Nonexistent method under negotiated capability raises UnknownMethodError."""
        session = self.server.negotiate({CAPABILITY_TOOLS})
        with self.assertRaises(UnknownMethodError):
            session.dispatch(CAPABILITY_TOOLS, "non_existent_method")


if __name__ == "__main__":
    unittest.main()
