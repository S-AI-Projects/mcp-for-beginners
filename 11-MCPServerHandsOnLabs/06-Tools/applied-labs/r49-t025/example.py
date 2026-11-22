"""
Applied Lab R49-T025: Tool Routing with Pluggable Callable Interfaces and Local Adapters.

Lesson Context (11-MCPServerHandsOnLabs/06-Tools/README.md):
In production MCP servers, tools frequently depend on external enterprise systems
(such as remote database clusters, customer support CRMs, or calculation engines).
To maintain testability and component boundaries, external services must be placed
behind clean callable interfaces, with deterministic local adapters supplied for local testing.

Contract Requirements:
- Explicit intent rules:
    - 'help' -> 'support' handler
    - 'calculate' -> 'calculator' handler
    - 'unknown' -> 'fallback' handler
- Ambiguity resolution:
    - Ambiguous intent follows documented priority ('calculate' [Priority 1] > 'help' [Priority 2])
      and logs the chosen rule in an auditable decision record.
- Focus: Put external dependencies behind callable interfaces and supply deterministic local adapters.
- Explicitly identify which real-service behaviors this mock adapter does NOT establish.

Simplification Boundary:
This lab implements deterministic local adapters that fulfill the interface contracts
in-memory without network calls or cloud dependencies.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, Protocol, Tuple, Union
import uuid
import re


# ---------------------------------------------------------------------------
# Real-Service Behaviors Not Established by the Mock Adapters
# ---------------------------------------------------------------------------

UNESTABLISHED_REAL_SERVICE_BEHAVIORS: List[str] = [
    "Network latency, packet drops, transport timeouts, and partial TCP stream disconnections.",
    "HTTP protocol semantics (401 Unauthorized, 403 Forbidden, 429 Rate Limiting, 503 Overloaded).",
    "Authentication handshakes, dynamic token expiration, and OAuth2/Entra ID credential renewals.",
    "Distributed concurrency, thread contention, and connection pool exhaustion.",
    "Non-deterministic semantic LLM understanding and open-ended generative reasoning."
]


# ---------------------------------------------------------------------------
# Public Data Contracts
# ---------------------------------------------------------------------------

@dataclass
class ToolRequest:
    """Incoming tool request payload."""
    query: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))


@dataclass
class AuditRecord:
    """Auditable decision record capturing routing and resolution metadata."""
    request_id: str
    raw_query: str
    matched_intents: List[str]
    selected_intent: str
    resolution_rule: str
    handler_name: str
    timestamp: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "request_id": self.request_id,
            "raw_query": self.raw_query,
            "matched_intents": self.matched_intents,
            "selected_intent": self.selected_intent,
            "resolution_rule": self.resolution_rule,
            "handler_name": self.handler_name,
            "timestamp": self.timestamp,
        }


@dataclass
class ToolResult:
    """Standardized MCP tool execution result from Lab 06."""
    success: bool
    data: Any = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    execution_time_ms: Optional[float] = None


# ---------------------------------------------------------------------------
# External Dependency Callable Interfaces
# ---------------------------------------------------------------------------

class ISupportService(Protocol):
    """Callable interface for external support knowledge base / ticketing service."""
    def get_support(self, query: str) -> Dict[str, Any]:
        ...


class ICalculatorService(Protocol):
    """Callable interface for external computation / arithmetic service."""
    def compute(self, query: str) -> Dict[str, Any]:
        ...


# ---------------------------------------------------------------------------
# Deterministic Local Adapters (Supplied Implementations)
# ---------------------------------------------------------------------------

class DeterministicSupportAdapter:
    """Local deterministic adapter implementing ISupportService without external APIs."""

    def __init__(self):
        self.invocation_count = 0

    def get_support(self, query: str) -> Dict[str, Any]:
        self.invocation_count += 1
        return {
            "service": "DeterministicSupportAdapter",
            "message": "Local support guidance: tutorials, FAQs, and documentation are available.",
            "query": query,
            "adapter_type": "deterministic_local_mock"
        }


class DeterministicCalculatorAdapter:
    """Local deterministic adapter implementing ICalculatorService without external APIs."""

    def __init__(self):
        self.invocation_count = 0

    def compute(self, query: str) -> Dict[str, Any]:
        self.invocation_count += 1
        # Simple deterministic arithmetic parsing
        expr_match = re.search(r"(\d+(?:\.\d+)?)\s*([\+\-\*\/])\s*(\d+(?:\.\d+)?)", query)
        computed = None
        if expr_match:
            a, op, b = float(expr_match.group(1)), expr_match.group(2), float(expr_match.group(3))
            if op == "+":
                computed = a + b
            elif op == "-":
                computed = a - b
            elif op == "*":
                computed = a * b
            elif op == "/":
                computed = a / b if b != 0 else "Error: Division by zero"

        return {
            "service": "DeterministicCalculatorAdapter",
            "result": computed if computed is not None else 0.0,
            "query": query,
            "adapter_type": "deterministic_local_mock"
        }


# ---------------------------------------------------------------------------
# Intent Rules and Precedence
# ---------------------------------------------------------------------------

@dataclass
class IntentRule:
    intent_name: str
    handler_name: str
    patterns: List[str]
    priority: int  # Lower number = higher priority
    description: str

    def matches(self, query: str) -> bool:
        normalized = query.lower()
        return any(re.search(rf"\b{re.escape(p.lower())}\b", normalized) for p in self.patterns)


DEFAULT_RULES: List[IntentRule] = [
    IntentRule(
        intent_name="calculate",
        handler_name="calculator",
        patterns=["calculate", "calc", "sum", "multiply", "divide", "add", "subtract", "math"],
        priority=1,
        description="Routes computational queries to calculator adapter."
    ),
    IntentRule(
        intent_name="help",
        handler_name="support",
        patterns=["help", "support", "assist", "guide", "faq", "info"],
        priority=2,
        description="Routes advisory queries to support adapter."
    ),
]


# ---------------------------------------------------------------------------
# Tool Router
# ---------------------------------------------------------------------------

class ToolRouter:
    """
    Routes requests using explicit intent rules, documented priority for ambiguity,
    and dispatches to handlers backed by pluggable callable interfaces.
    """

    def __init__(
        self,
        support_service: Optional[ISupportService] = None,
        calculator_service: Optional[ICalculatorService] = None,
        rules: Optional[List[IntentRule]] = None
    ):
        self.support_service = support_service or DeterministicSupportAdapter()
        self.calculator_service = calculator_service or DeterministicCalculatorAdapter()
        self.rules = sorted(rules or DEFAULT_RULES, key=lambda r: r.priority)
        self.audit_log: List[AuditRecord] = []

    def resolve_intent(self, query: str) -> Tuple[List[str], str, str, str]:
        matched = [r for r in self.rules if r.matches(query)]
        matched_intents = [r.intent_name for r in matched]

        if not matched:
            return (
                [],
                "unknown",
                "default_fallback: no explicit intent rule matched",
                "fallback"
            )

        if len(matched) == 1:
            chosen = matched[0]
            return (
                matched_intents,
                chosen.intent_name,
                f"exact_rule_match: rule '{chosen.intent_name}' matched uniquely",
                chosen.handler_name
            )

        # Ambiguous resolution
        chosen = matched[0]
        suppressed = [r.intent_name for r in matched[1:]]
        rule_desc = (
            f"priority_resolution: '{chosen.intent_name}' (priority {chosen.priority}) "
            f"selected over {suppressed} following documented precedence"
        )
        return (
            matched_intents,
            chosen.intent_name,
            rule_desc,
            chosen.handler_name
        )

    def dispatch(self, request: ToolRequest) -> ToolResult:
        matched_intents, selected_intent, resolution_rule, handler_name = self.resolve_intent(request.query)

        now_utc = datetime.now(timezone.utc).isoformat()
        audit = AuditRecord(
            request_id=request.request_id,
            raw_query=request.query,
            matched_intents=matched_intents,
            selected_intent=selected_intent,
            resolution_rule=resolution_rule,
            handler_name=handler_name,
            timestamp=now_utc,
        )
        self.audit_log.append(audit)

        # Dispatch to handler backed by interface adapter
        if handler_name == "support":
            service_resp = self.support_service.get_support(request.query)
            result = ToolResult(success=True, data=service_resp)
        elif handler_name == "calculator":
            service_resp = self.calculator_service.compute(request.query)
            result = ToolResult(success=True, data=service_resp)
        else:
            result = ToolResult(
                success=True,
                data={
                    "service": "FallbackHandler",
                    "message": "Unrecognized intent. Available tools are 'support' and 'calculator'.",
                    "query": request.query
                }
            )

        result.metadata = {"audit": audit.to_dict()}
        return result


# ---------------------------------------------------------------------------
# CLI / Demonstration
# ---------------------------------------------------------------------------

def run_demo() -> None:
    router = ToolRouter()
    scenarios = [
        ("Normal - Support", "Please help me understand how this tool works"),
        ("Normal - Calculator", "Can you calculate 25 * 4 for the quarterly report?"),
        ("Ambiguous - Calculate + Help", "Please help me calculate total margin: 100 - 45"),
        ("Failure/Unknown - Fallback", "Check the weather in Seattle tomorrow"),
    ]

    print("=" * 80)
    print("Applied Lab R49-T025: Interface-Backed Tool Routing & Adapter Demo")
    print("=" * 80)
    for label, query in scenarios:
        req = ToolRequest(query=query)
        result = router.dispatch(req)
        audit = result.metadata["audit"]
        print(f"\n[{label}]")
        print(f"  Input:           '{req.query}'")
        print(f"  Matched:         {audit['matched_intents']}")
        print(f"  Selected:        {audit['selected_intent']}")
        print(f"  Handler:         {audit['handler_name']}")
        print(f"  Resolution Rule: {audit['resolution_rule']}")
        print(f"  Adapter Data:    {result.data}")

    print("\n" + "=" * 80)
    print("Behaviors NOT established by this local adapter:")
    for idx, item in enumerate(UNESTABLISHED_REAL_SERVICE_BEHAVIORS, 1):
        print(f"  {idx}. {item}")
    print("=" * 80)


if __name__ == "__main__":
    run_demo()
