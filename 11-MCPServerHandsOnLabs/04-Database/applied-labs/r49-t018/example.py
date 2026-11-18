"""Capability negotiation, pre-dispatch gating, and failure recovery for Database MCP servers.

Task R49-T018: Capability negotiation — failure and recovery example.
"""

from typing import Any, Callable, Dict, Iterable, Optional, Set


class CapabilityNotNegotiatedError(PermissionError):
    """Raised when an unnegotiated capability is invoked."""
    pass


class InvalidQueryError(ValueError):
    """Raised when query execution encounters missing or invalid arguments."""
    pass


def negotiate_capabilities(
    client_capabilities: Iterable[str],
    server_capabilities: Iterable[str],
) -> Set[str]:
    """Intersect client and server capability collections."""
    if not isinstance(client_capabilities, (set, list, tuple)):
        raise TypeError("client_capabilities must be an iterable collection")
    if not isinstance(server_capabilities, (set, list, tuple)):
        raise TypeError("server_capabilities must be an iterable collection")
    return set(client_capabilities).intersection(set(server_capabilities))


class DatabaseServerSession:
    """Simulated Database MCP server session with capability gating and recovery."""

    def __init__(self, server_capabilities: Optional[Iterable[str]] = None):
        self.server_capabilities = set(server_capabilities or {"tools", "prompts"})
        self.negotiated_capabilities: Optional[Set[str]] = None
        self._handlers: Dict[str, Callable[..., Any]] = {}
        self._register_default_handlers()

    def _register_default_handlers(self) -> None:
        self._handlers["tools"] = self._mock_database_tool

    def negotiate(self, client_capabilities: Iterable[str]) -> Set[str]:
        """Intersect capabilities during initialization."""
        self.negotiated_capabilities = negotiate_capabilities(
            client_capabilities, self.server_capabilities
        )
        return set(self.negotiated_capabilities)

    def dispatch(self, capability: str, action: str, **kwargs: Any) -> Dict[str, Any]:
        """Dispatch operation if capability was negotiated; gate otherwise."""
        if self.negotiated_capabilities is None:
            raise RuntimeError("Capabilities have not been negotiated yet")

        if capability not in self.negotiated_capabilities:
            raise CapabilityNotNegotiatedError(
                f"Capability '{capability}' was not negotiated. "
                f"Negotiated capabilities: {sorted(self.negotiated_capabilities)}"
            )

        handler = self._handlers.get(capability)
        if not handler:
            raise ValueError(f"No handler registered for capability '{capability}'")

        return handler(action, **kwargs)

    @staticmethod
    def _mock_database_tool(action: str, **kwargs: Any) -> Dict[str, Any]:
        """Simulate database tool with multi-tenant store_id validation."""
        if action == "query_products":
            store_id = kwargs.get("store_id")
            sql = kwargs.get("sql")

            if not store_id or not str(store_id).strip():
                raise InvalidQueryError("Missing required parameter: 'store_id' is mandatory for multi-tenant isolation")
            if not sql or not str(sql).strip():
                raise InvalidQueryError("Missing required parameter: 'sql' query cannot be empty")

            return {
                "status": "success",
                "store_id": store_id,
                "rows": [
                    {"product_id": 1, "name": "Running Shoes", "stock": 42},
                    {"product_id": 2, "name": "Trail Jacket", "stock": 15},
                ],
                "row_count": 2,
            }

        return {"status": "success", "action": action, "data": kwargs}


def main() -> None:
    """Run demonstration with capability negotiation, unnegotiated rejection, and failure recovery."""
    print("=== Database Capability Negotiation & Recovery Demo (R49-T018) ===")

    # 1. Negotiate capabilities: client {tools, resources} vs server {tools, prompts} -> {tools}
    client_caps = {"tools", "resources"}
    server_caps = {"tools", "prompts"}
    session = DatabaseServerSession(server_capabilities=server_caps)
    negotiated = session.negotiate(client_caps)
    print(f"Client capabilities: {sorted(client_caps)}")
    print(f"Server capabilities: {sorted(server_caps)}")
    print(f"Negotiated capabilities: {sorted(negotiated)}")

    # 2. Reject unnegotiated capability 'resources' before dispatch
    print("\n[Step 1] Attempting to invoke unnegotiated capability 'resources'...")
    try:
        session.dispatch("resources", "read_schema", table="products")
        print("ERROR: Unnegotiated capability was not rejected!")
    except CapabilityNotNegotiatedError as exc:
        print(f"Successfully rejected before dispatch: {exc}")

    # 3. Exercise invalid/missing data failure: missing store_id
    print("\n[Step 2] Executing query with missing 'store_id'...")
    try:
        session.dispatch("tools", "query_products", sql="SELECT * FROM products")
        print("ERROR: Missing parameter was not rejected!")
    except InvalidQueryError as exc:
        print(f"Caught documented missing-data error: {exc}")

    # 4. Demonstrate recovery on the next valid input
    print("\n[Step 3] Recovering on next valid input (supplying store_id)...")
    recovered_res = session.dispatch(
        "tools",
        "query_products",
        store_id="store-east-01",
        sql="SELECT * FROM products",
    )
    print(f"Recovery successful! Retrieved {recovered_res['row_count']} rows for store {recovered_res['store_id']}.")

    print("\nDemo completed successfully. No live PostgreSQL instance or network required.")


if __name__ == "__main__":
    main()
