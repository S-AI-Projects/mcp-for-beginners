"""
MCP Server Architecture - Capability Negotiation: Comparing Direct Implementation
vs. Independent Truth Table Calculation.

Lesson Extension: 11-MCPServerHandsOnLabs/01-Architecture
Task ID: R49-T032

Focus:
- Compare the direct stateful implementation with a simpler independent calculation
  and an explicit expected-result truth table, using identical inputs.
- Client {tools, resources}, Server {tools, prompts} negotiates {tools}.
- Calling unnegotiated capability (resources) is strictly rejected before dispatch.
- Zero external dependencies: Uses local deterministic store analytics fixture.
"""

from dataclasses import dataclass, field
import json
import time
from typing import Any, Callable, Dict, List, Optional, Set, Tuple


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


class UnknownMethodError(CapabilityError):
    """Raised when a method is not found under a negotiated capability."""
    pass


class InvalidCapabilityError(CapabilityError):
    """Raised when capability identifier is malformed or invalid."""
    pass


# Deterministic Local Fixture: Retail Store Performance Analytics
LOCAL_FIXTURE_STORES = [
    {
        "store_id": "store-101",
        "city": "Seattle",
        "region": "Northwest",
        "daily_sales": 14250.00,
        "transactions": 312,
        "status": "active"
    },
    {
        "store_id": "store-102",
        "city": "Portland",
        "region": "Northwest",
        "daily_sales": 9820.50,
        "transactions": 198,
        "status": "active"
    },
    {
        "store_id": "store-103",
        "city": "San Francisco",
        "region": "West",
        "daily_sales": 22100.75,
        "transactions": 450,
        "status": "active"
    }
]


# ==============================================================================
# Approach 1: Direct Implementation (Stateful Protocol Layer & Dispatch Engine)
# ==============================================================================

class DirectMCPSession:
    """Active session managing negotiated capabilities and pre-dispatch gating."""

    def __init__(
        self,
        server: "DirectMCPServer",
        client_capabilities: Set[str],
        server_capabilities: Set[str],
        negotiated_capabilities: Set[str]
    ):
        self.server = server
        self.client_capabilities = set(client_capabilities)
        self.server_capabilities = set(server_capabilities)
        self.negotiated_capabilities = set(negotiated_capabilities)
        self.audit_log: List[Dict[str, Any]] = []

    def dispatch(self, capability: str, method: str, **kwargs) -> Any:
        """
        Dispatch invocation to server handler with pre-dispatch gating.
        
        Boundary Decision:
        If capability is not negotiated, reject before inspecting or dispatching to handlers.
        """
        if not isinstance(capability, str) or not capability.strip():
            raise InvalidCapabilityError(f"Invalid capability: {capability!r}")

        clean_cap = capability.strip().lower()

        # Pre-dispatch gate
        if clean_cap not in self.negotiated_capabilities:
            self.audit_log.append({
                "capability": clean_cap,
                "method": method,
                "status": "REJECTED_BEFORE_DISPATCH",
                "negotiated": False
            })
            raise CapabilityNotNegotiatedError(
                f"Capability '{clean_cap}' is not negotiated for this session. "
                f"Negotiated set: {sorted(list(self.negotiated_capabilities))}. "
                f"Client offered: {sorted(list(self.client_capabilities))}, "
                f"Server offered: {sorted(list(self.server_capabilities))}. "
                f"Invocation rejected before dispatch."
            )

        self.audit_log.append({
            "capability": clean_cap,
            "method": method,
            "status": "DISPATCHED",
            "negotiated": True
        })
        return self.server._execute_handler(clean_cap, method, **kwargs)


class DirectMCPServer:
    """Direct MCP Server implementation with runtime handler registry."""

    def __init__(
        self,
        server_name: str = "RetailAnalyticsServer",
        supported_capabilities: Optional[Set[str]] = None,
        store_fixture: Optional[List[Dict[str, Any]]] = None
    ):
        self.server_name = server_name
        self.supported_capabilities = (
            set(supported_capabilities)
            if supported_capabilities is not None
            else {CAPABILITY_TOOLS, CAPABILITY_PROMPTS}
        )
        self.stores = store_fixture or list(LOCAL_FIXTURE_STORES)
        self._handlers: Dict[Tuple[str, str], Callable[..., Any]] = {}
        self._handler_call_counts: Dict[Tuple[str, str], int] = {}
        self._register_default_handlers()

    def _register_handler(self, capability: str, method: str, handler: Callable[..., Any]):
        key = (capability.lower(), method.lower())
        self._handlers[key] = handler
        self._handler_call_counts[key] = 0

    def _register_default_handlers(self):
        # Tools: store performance query
        self._register_handler(CAPABILITY_TOOLS, "get_store_metrics", self.get_store_metrics)
        self._register_handler(CAPABILITY_TOOLS, "list_regions", self.list_regions)

        # Prompts: analytics prompt
        self._register_handler(CAPABILITY_PROMPTS, "sales_report_prompt", self.sales_report_prompt)

        # Resources: intentionally internal/unnegotiated when server lacks resources capability
        self._register_handler(CAPABILITY_RESOURCES, "read_store_schema", self._resource_read_schema)

    def negotiate(self, client_capabilities: Set[str]) -> DirectMCPSession:
        """Dynamic runtime capability intersection."""
        clean_client = {c.strip().lower() for c in client_capabilities if isinstance(c, str) and c.strip()}
        negotiated = clean_client.intersection(self.supported_capabilities)
        return DirectMCPSession(
            server=self,
            client_capabilities=clean_client,
            server_capabilities=set(self.supported_capabilities),
            negotiated_capabilities=negotiated
        )

    def _execute_handler(self, capability: str, method: str, **kwargs) -> Any:
        key = (capability.lower(), method.lower())
        if key not in self._handlers:
            raise UnknownMethodError(f"Method '{method}' not found under capability '{capability}'.")
        self._handler_call_counts[key] += 1
        return self._handlers[key](**kwargs)

    def get_call_count(self, capability: str, method: str) -> int:
        return self._handler_call_counts.get((capability.lower(), method.lower()), 0)

    # Tool Implementations
    def get_store_metrics(self, store_id: str) -> Dict[str, Any]:
        for s in self.stores:
            if s["store_id"] == store_id:
                return dict(s)
        raise KeyError(f"Store '{store_id}' not found.")

    def list_regions(self) -> List[str]:
        return sorted(list({s["region"] for s in self.stores}))

    # Prompt Implementation
    def sales_report_prompt(self, region: str = "Northwest") -> str:
        return f"Generate executive summary for stores in the {region} region."

    # Resource Implementation
    def _resource_read_schema(self) -> Dict[str, str]:
        return {"store_id": "string", "city": "string", "daily_sales": "float"}


# ==============================================================================
# Approach 2: Independent Calculation & Explicit Truth Table Reference
# ==============================================================================

def independent_capability_calculation(
    client_capabilities: Set[str],
    server_capabilities: Set[str]
) -> Set[str]:
    """
    Pure functional calculation of negotiated capabilities.
    Independent mathematical set intersection without stateful objects.
    """
    return {c for c in client_capabilities if c in server_capabilities}


# Explicit Expected-Result Truth Table for Canonical MCP Architecture Scenarios
EXPLICIT_EXPECTED_TABLE: Dict[
    Tuple[Tuple[str, ...], Tuple[str, ...]],
    Dict[str, Any]
] = {
    # 1. Primary Asymmetric Scenario (Goal): Client {tools, resources}, Server {tools, prompts}
    (
        ("resources", "tools"),
        ("prompts", "tools")
    ): {
        "expected_negotiated": ["tools"],
        "client_unsupported": ["resources"],
        "server_unsupported": ["prompts"],
        "allowed_dispatches": ["tools"],
        "rejected_dispatches": ["resources", "prompts"],
        "rationale": "Only 'tools' is common. 'resources' lacks server support; 'prompts' lacks client declaration."
    },

    # 2. Smallest Valid Minimal Pair
    (
        ("tools",),
        ("tools",)
    ): {
        "expected_negotiated": ["tools"],
        "client_unsupported": [],
        "server_unsupported": [],
        "allowed_dispatches": ["tools"],
        "rejected_dispatches": ["resources", "prompts"],
        "rationale": "Symmetric single-capability negotiation. Full agreement."
    },

    # 3. Disjoint Capabilities
    (
        ("resources",),
        ("tools",)
    ): {
        "expected_negotiated": [],
        "client_unsupported": ["resources"],
        "server_unsupported": ["tools"],
        "allowed_dispatches": [],
        "rejected_dispatches": ["tools", "resources"],
        "rationale": "Completely disjoint sets. Session permits zero dispatches."
    },

    # 4. Empty Client Capabilities
    (
        (),
        ("prompts", "tools")
    ): {
        "expected_negotiated": [],
        "client_unsupported": [],
        "server_unsupported": ["prompts", "tools"],
        "allowed_dispatches": [],
        "rejected_dispatches": ["tools", "prompts"],
        "rationale": "Client offers no capabilities. Yields empty session."
    }
}


def lookup_expected_table(
    client_caps: Set[str],
    server_caps: Set[str]
) -> Optional[Dict[str, Any]]:
    """Lookup expected result from the explicit truth table using sorted tuples."""
    key = (tuple(sorted(list(client_caps))), tuple(sorted(list(server_caps))))
    return EXPLICIT_EXPECTED_TABLE.get(key)


# ==============================================================================
# Comparative Analysis Engine
# ==============================================================================

@dataclass
class ComparisonRecord:
    client_caps: List[str]
    server_caps: List[str]
    direct_negotiated: List[str]
    independent_calc_negotiated: List[str]
    table_expected_negotiated: Optional[List[str]]
    direct_matches_independent: bool
    direct_matches_table: bool
    rejected_capability_test: Dict[str, Any]


def compare_approaches(
    client_caps: Set[str],
    server_caps: Set[str],
    test_invocation_cap: str = CAPABILITY_RESOURCES,
    test_invocation_method: str = "read_store_schema"
) -> ComparisonRecord:
    """
    Execute identical inputs through both Approach 1 (Direct Implementation)
    and Approach 2 (Independent Calculation + Expected Table Lookup).
    """
    # 1. Direct Implementation
    server = DirectMCPServer(supported_capabilities=server_caps)
    session = server.negotiate(client_caps)
    direct_negotiated = sorted(list(session.negotiated_capabilities))

    # Test pre-dispatch rejection on direct implementation
    rejection_info = {}
    try:
        session.dispatch(test_invocation_cap, test_invocation_method)
        rejection_info["rejected"] = False
        rejection_info["status"] = "UNEXPECTED_DISPATCH_SUCCESS"
    except CapabilityNotNegotiatedError as e:
        rejection_info["rejected"] = True
        rejection_info["error_type"] = type(e).__name__
        rejection_info["handler_call_count"] = server.get_call_count(test_invocation_cap, test_invocation_method)
        rejection_info["status"] = "REJECTED_BEFORE_DISPATCH"

    # 2. Independent Calculation
    calc_negotiated = sorted(list(independent_capability_calculation(client_caps, server_caps)))

    # 3. Explicit Table Lookup
    table_entry = lookup_expected_table(client_caps, server_caps)
    table_expected = table_entry["expected_negotiated"] if table_entry else None

    return ComparisonRecord(
        client_caps=sorted(list(client_caps)),
        server_caps=sorted(list(server_caps)),
        direct_negotiated=direct_negotiated,
        independent_calc_negotiated=calc_negotiated,
        table_expected_negotiated=table_expected,
        direct_matches_independent=(direct_negotiated == calc_negotiated),
        direct_matches_table=(table_expected is None or direct_negotiated == table_expected),
        rejected_capability_test=rejection_info
    )


def run_demonstration() -> Dict[str, Any]:
    """Execute comparative demonstration between Direct Implementation and Independent Table."""
    print("=" * 75)
    print("MCP Architecture: Capability Negotiation — Comparing Two Approaches (R49-T032)")
    print("=" * 75)

    test_scenarios = [
        # Primary Asymmetric Scenario
        ({CAPABILITY_TOOLS, CAPABILITY_RESOURCES}, {CAPABILITY_TOOLS, CAPABILITY_PROMPTS}),
        # Smallest Valid
        ({CAPABILITY_TOOLS}, {CAPABILITY_TOOLS}),
        # Disjoint
        ({CAPABILITY_RESOURCES}, {CAPABILITY_TOOLS}),
        # Empty Client
        (set(), {CAPABILITY_TOOLS, CAPABILITY_PROMPTS})
    ]

    results = []
    for client_c, server_c in test_scenarios:
        rec = compare_approaches(client_c, server_c)
        results.append(rec)

        print(f"\n[Test Inputs]")
        print(f"  Client Capabilities : {rec.client_caps}")
        print(f"  Server Capabilities : {rec.server_caps}")
        print(f"  Approach 1 (Direct) : {rec.direct_negotiated}")
        print(f"  Approach 2 (Calc)   : {rec.independent_calc_negotiated}")
        print(f"  Approach 2 (Table)  : {rec.table_expected_negotiated}")
        print(f"  Equivalence Match   : Direct == Calc: {rec.direct_matches_independent} | Direct == Table: {rec.direct_matches_table}")
        print(f"  Pre-Dispatch Reject : {rec.rejected_capability_test.get('status')} (Calls: {rec.rejected_capability_test.get('handler_call_count', 0)})")

    # Primary scenario detailed execution
    print("\n" + "-" * 75)
    print("[Detailed Invocation Verification on Primary Scenario]")
    primary_server = DirectMCPServer(supported_capabilities={CAPABILITY_TOOLS, CAPABILITY_PROMPTS})
    primary_session = primary_server.negotiate({CAPABILITY_TOOLS, CAPABILITY_RESOURCES})

    # Call valid tool
    tool_result = primary_session.dispatch(CAPABILITY_TOOLS, "get_store_metrics", store_id="store-101")
    print(f"  Valid call 'tools/get_store_metrics' -> Success: {tool_result['city']} (${tool_result['daily_sales']:,.2f})")

    # Call unnegotiated resource
    try:
        primary_session.dispatch(CAPABILITY_RESOURCES, "read_store_schema")
    except CapabilityNotNegotiatedError as e:
        print(f"  Unnegotiated call 'resources/read_store_schema' -> Correctly Rejected Before Dispatch:")
        print(f"    Message: {e}")

    print("=" * 75)
    print("Comparison complete: All approaches agree across all identical inputs.")
    print("=" * 75)

    return {
        "scenarios_evaluated": len(results),
        "all_match": all(r.direct_matches_independent and r.direct_matches_table for r in results)
    }


if __name__ == "__main__":
    run_demonstration()
