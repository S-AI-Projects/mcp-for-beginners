"""Unit tests for R49-T018 capability negotiation, feature gating, and failure recovery."""

import unittest

from example import (
    CapabilityNotNegotiatedError,
    DatabaseServerSession,
    InvalidQueryError,
    negotiate_capabilities,
)


class TestDatabaseCapabilityNegotiation(unittest.TestCase):
    """Test suite verifying capability intersection, pre-dispatch rejection, and recovery."""

    def test_negotiation_exact_contract(self):
        """Client {tools, resources} and server {tools, prompts} negotiates {tools}."""
        negotiated = negotiate_capabilities({"tools", "resources"}, {"tools", "prompts"})
        self.assertEqual(negotiated, {"tools"})

    def test_calling_unnegotiated_resources_rejected_before_dispatch(self):
        """Calling 'resources' capability is rejected before dispatch."""
        session = DatabaseServerSession(server_capabilities={"tools", "prompts"})
        session.negotiate({"tools", "resources"})

        with self.assertRaises(CapabilityNotNegotiatedError) as ctx:
            session.dispatch("resources", "read_schema", table="products")
        self.assertIn("resources", str(ctx.exception))

    def test_documented_missing_data_failure_and_clean_recovery(self):
        """A documented missing-data failure occurs, followed by clean recovery on valid input."""
        session = DatabaseServerSession(server_capabilities={"tools", "prompts"})
        session.negotiate({"tools", "resources"})

        # Failure: missing store_id
        with self.assertRaises(InvalidQueryError) as ctx:
            session.dispatch("tools", "query_products", sql="SELECT * FROM products")
        self.assertIn("store_id", str(ctx.exception))

        # Recovery on next valid input
        res = session.dispatch(
            "tools",
            "query_products",
            store_id="store-101",
            sql="SELECT * FROM products",
        )
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["store_id"], "store-101")
        self.assertEqual(res["row_count"], 2)

    def test_empty_sql_query_fails(self):
        """Empty SQL query raises InvalidQueryError."""
        session = DatabaseServerSession(server_capabilities={"tools", "prompts"})
        session.negotiate({"tools"})

        with self.assertRaises(InvalidQueryError):
            session.dispatch("tools", "query_products", store_id="store-1", sql="")

    def test_dispatch_before_negotiation_fails(self):
        """Dispatch before negotiate() raises RuntimeError."""
        session = DatabaseServerSession(server_capabilities={"tools", "prompts"})
        with self.assertRaises(RuntimeError):
            session.dispatch("tools", "query_products", store_id="store-1", sql="SELECT 1")


if __name__ == "__main__":
    unittest.main()
