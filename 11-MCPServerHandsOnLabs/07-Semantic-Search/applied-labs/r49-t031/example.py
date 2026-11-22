"""
MCP Semantic Search Server - Capability Negotiation and Feature Gating.

Lesson Extension: 11-MCPServerHandsOnLabs/07-Semantic-Search
Task ID: R49-T031

This module demonstrates capability negotiation between an MCP Client and Server:
- Client declares supported capabilities: e.g. {"tools", "resources"}
- Server declares supported capabilities: e.g. {"tools", "prompts"}
- Negotiated capabilities: client_capabilities ∩ server_capabilities -> {"tools"}
- Pre-dispatch gating: Calling any unnegotiated capability (e.g. "resources") is
  strictly rejected before dispatch, ensuring security and protocol conformance.
- Local Fixture: Self-contained zero-dependency deterministic catalog and token-based
  similarity simulation (no external models, GPUs, or network services).
"""

from dataclasses import dataclass, field
import math
import re
from typing import Any, Callable, Dict, List, Optional, Set, Tuple


# Standard MCP Capability Names
CAPABILITY_TOOLS = "tools"
CAPABILITY_RESOURCES = "resources"
CAPABILITY_PROMPTS = "prompts"
CAPABILITY_LOGGING = "logging"

ALL_STANDARD_CAPABILITIES = {
    CAPABILITY_TOOLS,
    CAPABILITY_RESOURCES,
    CAPABILITY_PROMPTS,
    CAPABILITY_LOGGING,
}


class CapabilityError(Exception):
    """Base exception for capability negotiation and dispatch errors."""
    pass


class CapabilityNotNegotiatedError(CapabilityError):
    """Raised when an invocation targets a capability not in the negotiated set."""
    pass


class UninitializedSessionError(CapabilityError):
    """Raised when dispatch is attempted before capability negotiation occurs."""
    pass


class UnknownMethodError(CapabilityError):
    """Raised when a method is not found within a negotiated capability."""
    pass


class InvalidCapabilityError(CapabilityError):
    """Raised when an invalid capability identifier is provided."""
    pass


# Deterministic Local Fixture (Zero external dependencies)
LOCAL_FIXTURE_PRODUCTS = [
    {
        "id": "prod-001",
        "name": "Trail Runner Pro Shoes",
        "category": "footwear",
        "description": "Durable all-weather trail running shoes with rugged grip and waterproof lining.",
        "tags": ["running", "shoes", "trail", "waterproof", "outdoor"]
    },
    {
        "id": "prod-002",
        "name": "Ultra Lightweight Road Shoes",
        "category": "footwear",
        "description": "Breathable high-speed road running shoes engineered for marathons and pavements.",
        "tags": ["running", "shoes", "road", "lightweight", "marathon"]
    },
    {
        "id": "prod-003",
        "name": "Alpine Trekking Backpack",
        "category": "gear",
        "description": "Ergonomic 45L hiking backpack with hydration pack compatibility and rain cover.",
        "tags": ["backpack", "hiking", "trekking", "gear", "outdoor"]
    },
    {
        "id": "prod-004",
        "name": "Thermal Polar Fleece Jacket",
        "category": "apparel",
        "description": "Warm insulating fleece jacket suitable for cold weather running and hiking.",
        "tags": ["jacket", "apparel", "thermal", "fleece", "running"]
    }
]


def _tokenize(text: str) -> List[str]:
    """Tokenize text into lowercase alphanumeric words."""
    return re.findall(r"\b[a-zA-Z0-9_-]+\b", text.lower())


def simulated_semantic_similarity(query: str, document_text: str) -> float:
    """
    Calculate deterministic cosine-like term similarity between query and document.
    Simulates vector embedding cosine similarity without external models or GPUs.
    """
    q_tokens = _tokenize(query)
    d_tokens = _tokenize(document_text)
    if not q_tokens or not d_tokens:
        return 0.0

    q_counts: Dict[str, int] = {}
    for t in q_tokens:
        q_counts[t] = q_counts.get(t, 0) + 1

    d_counts: Dict[str, int] = {}
    for t in d_tokens:
        d_counts[t] = d_counts.get(t, 0) + 1

    all_terms = set(q_counts.keys()).union(set(d_counts.keys()))
    dot_product = sum(q_counts.get(t, 0) * d_counts.get(t, 0) for t in all_terms)

    q_norm = math.sqrt(sum(v * v for v in q_counts.values()))
    d_norm = math.sqrt(sum(v * v for v in d_counts.values()))

    if q_norm == 0.0 or d_norm == 0.0:
        return 0.0
    return round(dot_product / (q_norm * d_norm), 4)


@dataclass
class NegotiationReport:
    """Summary of capability negotiation results."""
    client_declared: Set[str]
    server_supported: Set[str]
    negotiated: Set[str]
    client_unsupported: Set[str] = field(init=False)
    server_unsupported: Set[str] = field(init=False)

    def __post_init__(self):
        self.client_unsupported = self.client_declared - self.negotiated
        self.server_unsupported = self.server_supported - self.negotiated

    def to_dict(self) -> Dict[str, Any]:
        return {
            "client_declared": sorted(list(self.client_declared)),
            "server_supported": sorted(list(self.server_supported)),
            "negotiated": sorted(list(self.negotiated)),
            "client_unsupported": sorted(list(self.client_unsupported)),
            "server_unsupported": sorted(list(self.server_unsupported)),
        }


class MCPSession:
    """
    Represents an active, negotiated MCP session between a client and server.
    Enforces pre-dispatch gating on every invocation.
    """

    def __init__(
        self,
        server: "MCPServer",
        client_capabilities: Set[str],
        server_capabilities: Set[str],
        negotiated_capabilities: Set[str],
    ):
        self.server = server
        self.client_capabilities = set(client_capabilities)
        self.server_capabilities = set(server_capabilities)
        self.negotiated_capabilities = set(negotiated_capabilities)
        self.dispatch_attempts: List[Dict[str, Any]] = []

    def dispatch(self, capability: str, method: str, **kwargs) -> Any:
        """
        Dispatch a request to the server under the specified capability.
        
        CRITICAL BOUNDARY DECISION:
        The capability must be verified against `negotiated_capabilities` BEFORE
        any dispatch or handler lookup. If unnegotiated, it is rejected immediately.
        """
        if not isinstance(capability, str) or not capability.strip():
            raise InvalidCapabilityError(f"Invalid capability format: {capability!r}")

        clean_cap = capability.strip().lower()
        self.dispatch_attempts.append({
            "capability": clean_cap,
            "method": method,
            "kwargs": kwargs,
            "negotiated": clean_cap in self.negotiated_capabilities
        })

        # Pre-dispatch gate: Reject if not negotiated
        if clean_cap not in self.negotiated_capabilities:
            raise CapabilityNotNegotiatedError(
                f"Capability '{clean_cap}' is not negotiated for this session. "
                f"Negotiated set: {sorted(list(self.negotiated_capabilities))}. "
                f"Client offered: {sorted(list(self.client_capabilities))}, "
                f"Server offered: {sorted(list(self.server_capabilities))}. "
                f"Invocation rejected before dispatch."
            )

        # Dispatch to server handler
        return self.server._execute_handler(clean_cap, method, **kwargs)


class MCPServer:
    """
    MCP Server supporting capability declaration, negotiation, and semantic search.
    """

    def __init__(
        self,
        server_name: str = "SemanticSearchMCPServer",
        supported_capabilities: Optional[Set[str]] = None,
        fixture_products: Optional[List[Dict[str, Any]]] = None,
    ):
        self.server_name = server_name
        self.supported_capabilities = (
            set(supported_capabilities)
            if supported_capabilities is not None
            else {CAPABILITY_TOOLS, CAPABILITY_PROMPTS}
        )
        self.products = fixture_products or list(LOCAL_FIXTURE_PRODUCTS)
        
        # Internal handlers registry
        self._handlers: Dict[Tuple[str, str], Callable[..., Any]] = {}
        self._execution_counters: Dict[Tuple[str, str], int] = {}
        self._register_default_handlers()

    def _register_handler(self, capability: str, method: str, handler: Callable[..., Any]):
        key = (capability.lower(), method.lower())
        self._handlers[key] = handler
        self._execution_counters[key] = 0

    def _register_default_handlers(self):
        # Tools handlers
        self._register_handler(CAPABILITY_TOOLS, "semantic_search", self.semantic_search)
        self._register_handler(CAPABILITY_TOOLS, "list_categories", self.list_categories)

        # Prompts handlers
        self._register_handler(CAPABILITY_PROMPTS, "search_prompt", self.search_prompt)

        # Resources handler (defined on server object to test that pre-dispatch gating
        # prevents execution even if a private implementation exists)
        self._register_handler(CAPABILITY_RESOURCES, "read_product", self._resource_read_product)

    def negotiate(self, client_capabilities: Set[str]) -> Tuple[MCPSession, NegotiationReport]:
        """
        Negotiate capabilities with a client and establish an active session.
        Negotiated set = client_capabilities ∩ server_supported_capabilities.
        """
        client_set = {c.strip().lower() for c in client_capabilities if isinstance(c, str) and c.strip()}
        negotiated_set = client_set.intersection(self.supported_capabilities)

        report = NegotiationReport(
            client_declared=client_set,
            server_supported=set(self.supported_capabilities),
            negotiated=negotiated_set,
        )

        session = MCPSession(
            server=self,
            client_capabilities=client_set,
            server_capabilities=set(self.supported_capabilities),
            negotiated_capabilities=negotiated_set,
        )
        return session, report

    def _execute_handler(self, capability: str, method: str, **kwargs) -> Any:
        """Internal execution after pre-dispatch capability gate has passed."""
        key = (capability.lower(), method.lower())
        if key not in self._handlers:
            raise UnknownMethodError(
                f"Method '{method}' not found under capability '{capability}'."
            )
        self._execution_counters[key] += 1
        return self._handlers[key](**kwargs)

    def get_handler_execution_count(self, capability: str, method: str) -> int:
        """Inspect handler execution count to verify pre-dispatch rejection."""
        key = (capability.lower(), method.lower())
        return self._execution_counters.get(key, 0)

    # --- Tool Implementations ---
    def semantic_search(
        self,
        query: str,
        top_k: int = 3,
        min_similarity: float = 0.05
    ) -> List[Dict[str, Any]]:
        """
        Perform local deterministic semantic search against the fixture products.
        """
        results = []
        for prod in self.products:
            searchable_text = f"{prod['name']} {prod['category']} {prod['description']} {' '.join(prod['tags'])}"
            score = simulated_semantic_similarity(query, searchable_text)
            if score >= min_similarity:
                results.append({
                    "id": prod["id"],
                    "name": prod["name"],
                    "category": prod["category"],
                    "similarity": score,
                    "description": prod["description"]
                })

        # Rank by similarity descending, then product ID ascending
        results.sort(key=lambda r: (-r["similarity"], r["id"]))
        return results[:top_k]

    def list_categories(self) -> List[str]:
        """List distinct categories available in fixture."""
        return sorted(list({p["category"] for p in self.products}))

    # --- Prompt Implementation ---
    def search_prompt(self, context: str = "retail") -> str:
        """Generate a prompt template for product semantic search."""
        return f"Find relevant {context} items matching the customer's intent."

    # --- Resource Handler (Intentionally private / unexposed in standard server caps) ---
    def _resource_read_product(self, product_id: str) -> Dict[str, Any]:
        """Read a product resource directly."""
        for p in self.products:
            if p["id"] == product_id:
                return p
        raise KeyError(f"Product {product_id} not found.")


def run_demonstration() -> Dict[str, Any]:
    """
    Run the demonstration covering:
    1. Smallest valid case (Client {tools}, Server {tools})
    2. Boundary case: Asymmetric negotiation (Client {tools, resources}, Server {tools, prompts})
    3. Boundary case: Disjoint capability sets (Client {resources}, Server {tools})
    4. Invalid case: Pre-dispatch rejection of resources invocation
    """
    demo_output: Dict[str, Any] = {}

    print("=" * 70)
    print("MCP Capability Negotiation & Boundary-Case Extension (R49-T031)")
    print("=" * 70)

    # 1. Asymmetric Case: Client {tools, resources}, Server {tools, prompts}
    server = MCPServer(
        server_name="SemanticSearchServer",
        supported_capabilities={CAPABILITY_TOOLS, CAPABILITY_PROMPTS}
    )
    client_caps = {CAPABILITY_TOOLS, CAPABILITY_RESOURCES}

    session, report = server.negotiate(client_caps)
    print(f"\n[Scenario 1: Asymmetric Negotiation]")
    print(f"  Client declared  : {sorted(list(report.client_declared))}")
    print(f"  Server supported : {sorted(list(report.server_supported))}")
    print(f"  Negotiated set   : {sorted(list(report.negotiated))}")
    print(f"  Client-unsupported: {sorted(list(report.client_unsupported))}")

    demo_output["asymmetric_negotiation"] = report.to_dict()

    # Dispatch valid tool
    print("\n  Invoking negotiated capability 'tools/semantic_search'...")
    search_results = session.dispatch(
        capability="tools",
        method="semantic_search",
        query="waterproof trail running shoes",
        top_k=2
    )
    print(f"  -> Success! Found {len(search_results)} items:")
    for item in search_results:
        print(f"     - {item['name']} (score: {item['similarity']})")
    demo_output["tools_invocation"] = {
        "status": "SUCCESS",
        "results": search_results
    }

    # Dispatch unnegotiated capability 'resources'
    print("\n  Invoking unnegotiated capability 'resources/read_product'...")
    try:
        session.dispatch(
            capability="resources",
            method="read_product",
            product_id="prod-001"
        )
        raise RuntimeError("Failed: Unnegotiated capability was not rejected!")
    except CapabilityNotNegotiatedError as exc:
        print(f"  -> Correctly rejected before dispatch!")
        print(f"     Reason: {exc}")
        demo_output["resources_rejection"] = {
            "status": "REJECTED_BEFORE_DISPATCH",
            "error_type": type(exc).__name__,
            "message": str(exc),
            "handler_execution_count": server.get_handler_execution_count("resources", "read_product")
        }

    # 2. Smallest Valid Case: Client {tools}, Server {tools}
    small_server = MCPServer(supported_capabilities={CAPABILITY_TOOLS})
    small_session, small_report = small_server.negotiate({CAPABILITY_TOOLS})
    small_res = small_session.dispatch(
        capability="tools",
        method="semantic_search",
        query="backpack",
        top_k=1
    )
    demo_output["smallest_valid_case"] = {
        "negotiated": sorted(list(small_report.negotiated)),
        "first_result": small_res[0]["name"] if small_res else None
    }

    # 3. Disjoint Case: Client {resources}, Server {tools}
    disjoint_session, disjoint_report = small_server.negotiate({CAPABILITY_RESOURCES})
    demo_output["disjoint_case"] = {
        "client": sorted(list(disjoint_report.client_declared)),
        "server": sorted(list(disjoint_report.server_supported)),
        "negotiated": sorted(list(disjoint_report.negotiated))
    }

    print("\n" + "=" * 70)
    print("All scenarios completed successfully.")
    print("=" * 70)
    return demo_output


if __name__ == "__main__":
    run_demonstration()
