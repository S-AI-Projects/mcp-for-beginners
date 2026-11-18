"""Capability negotiation and feature gating for MCP Semantic Search.

This module demonstrates capability discovery, intersection, and invocation
rejection for unnegotiated capabilities prior to dispatch.
"""

from typing import Any, Callable, Dict, Iterable, List, Optional, Set


class CapabilityNotNegotiatedError(PermissionError):
    """Raised when an action is dispatched to a capability that was not negotiated."""
    pass


def negotiate_capabilities(
    client_capabilities: Iterable[str],
    server_capabilities: Iterable[str],
) -> Set[str]:
    """Intersect client and server capability sets.

    Parameters:
        client_capabilities: Capabilities supported or requested by the client.
        server_capabilities: Capabilities supported by the server.

    Returns:
        The set of negotiated capabilities common to both client and server.
    """
    if not isinstance(client_capabilities, (set, list, tuple)):
        raise TypeError("client_capabilities must be an iterable collection of strings")
    if not isinstance(server_capabilities, (set, list, tuple)):
        raise TypeError("server_capabilities must be an iterable collection of strings")

    for item in client_capabilities:
        if not isinstance(item, str) or not item.strip():
            raise ValueError("All client capabilities must be non-empty strings")
    for item in server_capabilities:
        if not isinstance(item, str) or not item.strip():
            raise ValueError("All server capabilities must be non-empty strings")

    return set(client_capabilities).intersection(set(server_capabilities))


class SemanticSearchServerSession:
    """Simulated MCP server session managing capabilities and dispatch gating."""

    def __init__(self, server_capabilities: Optional[Iterable[str]] = None):
        if server_capabilities is None:
            self.server_capabilities = {"tools", "prompts"}
        else:
            self.server_capabilities = set(server_capabilities)

        self.negotiated_capabilities: Optional[Set[str]] = None
        self._handlers: Dict[str, Callable[..., Any]] = {}

        # Register default mock handlers for supported server capabilities
        self._register_default_handlers()

    def _register_default_handlers(self) -> None:
        """Register built-in mock handlers for semantic search tools and prompts."""
        self._handlers["tools"] = self._mock_tool_handler
        self._handlers["prompts"] = self._mock_prompt_handler

    def register_handler(self, capability: str, handler: Callable[..., Any]) -> None:
        """Register or override a capability handler."""
        self._handlers[capability] = handler

    def negotiate(self, client_capabilities: Iterable[str]) -> Set[str]:
        """Perform capability negotiation during session initialization.

        Parameters:
            client_capabilities: Capabilities presented by the client.

        Returns:
            The negotiated capability set (intersection of client and server).
        """
        self.negotiated_capabilities = negotiate_capabilities(
            client_capabilities, self.server_capabilities
        )
        return set(self.negotiated_capabilities)

    def dispatch(self, capability: str, method: str, **kwargs: Any) -> Any:
        """Dispatch an operation under the specified capability.

        Guards invocation by validating that the capability has been negotiated.
        Rejects unnegotiated capabilities before dispatching to any handler.

        Parameters:
            capability: The target capability (e.g. 'tools', 'resources').
            method: The method or action within the capability (e.g. 'semantic_search_products').
            kwargs: Method arguments.

        Returns:
            The handler execution result.

        Raises:
            RuntimeError: If negotiation has not occurred yet.
            CapabilityNotNegotiatedError: If the capability was not negotiated.
            ValueError: If no handler exists for a negotiated capability.
        """
        if self.negotiated_capabilities is None:
            raise RuntimeError(
                "Capabilities have not been negotiated yet. Call negotiate() during initialization."
            )

        if capability not in self.negotiated_capabilities:
            raise CapabilityNotNegotiatedError(
                f"Capability '{capability}' was not negotiated. "
                f"Negotiated capabilities: {sorted(self.negotiated_capabilities)}"
            )

        handler = self._handlers.get(capability)
        if not handler:
            raise ValueError(f"No handler registered for capability '{capability}'")

        return handler(method, **kwargs)

    @staticmethod
    def _mock_tool_handler(tool_name: str, **kwargs: Any) -> Dict[str, Any]:
        """Mock tool execution handler simulating semantic product search."""
        if tool_name == "semantic_search_products":
            query = kwargs.get("query", "")
            return {
                "tool": "semantic_search_products",
                "status": "success",
                "query": query,
                "matches": [
                    {
                        "product_id": "prod-101",
                        "product_name": "Trail Running Shoes",
                        "similarity_score": 0.89,
                    },
                    {
                        "product_id": "prod-204",
                        "product_name": "Comfort Walkers",
                        "similarity_score": 0.82,
                    },
                ],
            }
        return {
            "tool": tool_name,
            "status": "success",
            "kwargs": kwargs,
        }

    @staticmethod
    def _mock_prompt_handler(prompt_name: str, **kwargs: Any) -> Dict[str, Any]:
        """Mock prompt template handler."""
        return {
            "prompt": prompt_name,
            "status": "success",
            "template": f"Generated prompt for {prompt_name}",
        }


def main() -> None:
    """Run capability negotiation demonstration."""
    print("=== MCP Capability Negotiation Demo (R49-T011) ===")

    # 1. Define capabilities
    client_capabilities = {"tools", "resources"}
    server_capabilities = {"tools", "prompts"}

    print(f"Client capabilities: {sorted(client_capabilities)}")
    print(f"Server capabilities: {sorted(server_capabilities)}")

    # 2. Initialize session and negotiate capabilities
    session = SemanticSearchServerSession(server_capabilities=server_capabilities)
    negotiated = session.negotiate(client_capabilities)
    print(f"Negotiated capabilities: {sorted(negotiated)}")

    # 3. Invoke negotiated capability ('tools')
    print("\n[Action 1] Calling negotiated capability 'tools'...")
    tool_result = session.dispatch(
        capability="tools",
        method="semantic_search_products",
        query="comfortable running shoes",
    )
    print(f"Dispatch successful! Result: {tool_result}")

    # 4. Attempt to invoke unnegotiated capability ('resources')
    print("\n[Action 2] Calling unnegotiated capability 'resources'...")
    try:
        session.dispatch(
            capability="resources",
            method="read_resource",
            uri="resource://products/schema",
        )
        print("ERROR: Unnegotiated capability was not rejected!")
    except CapabilityNotNegotiatedError as exc:
        print(f"Successfully rejected before dispatch: {exc}")

    print("\nDemo completed successfully. No server process or external services contacted.")


if __name__ == "__main__":
    main()
