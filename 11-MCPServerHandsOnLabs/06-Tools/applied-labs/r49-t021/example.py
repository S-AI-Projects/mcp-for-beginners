"""
Applied Lab R49-T021: Intent-Based Tool Routing with Auditable Decision Records.

Lesson Context:
In 11-MCPServerHandsOnLabs/06-Tools/README.md, tools encapsulate distinct operational
responsibilities (database queries, schema introspection, analytics). When an AI
assistant receives a user request, it must safely and deterministically route that
request to the appropriate tool handler.

This module implements a minimal, complete, local routing system:
- Explicit rules:
    - 'help' -> 'support' handler
    - 'calculate' -> 'calculator' handler
    - 'unknown' -> 'fallback' handler
- Ambiguity resolution:
    - When multiple intents match (e.g., query contains both 'help' and 'calculate'),
      the router follows documented priority (calculate > help) and logs the chosen rule.
- Auditable Decision Record:
    - Every routing decision produces an audit log capturing raw query, candidate matches,
      applied resolution rule, selected intent, target handler, and timestamp.

Simplification Boundary:
This implementation uses deterministic pattern matching and in-memory audit logs.
In production, intent extraction might use an NLU classifier or LLM prompt router,
and decision records would be persisted to a distributed log/telemetry sink (e.g. Azure App Insights).
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional
import uuid
import re


# ---------------------------------------------------------------------------
# Public Input / Output Contracts (aligned with Lab 06 concepts)
# ---------------------------------------------------------------------------

@dataclass
class ToolRequest:
    """Public input contract: incoming request to be routed."""
    query: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))


@dataclass
class AuditRecord:
    """Public decision record: immutable audit trail for routing decisions."""
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
    """Public output contract: standardized tool execution result (from Lab 06)."""
    success: bool
    data: Any = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    execution_time_ms: Optional[float] = None


# ---------------------------------------------------------------------------
# Routing Rules and Priority
# ---------------------------------------------------------------------------

@dataclass
class IntentRule:
    """Explicit intent rule with documented precedence."""
    intent_name: str
    handler_name: str
    patterns: List[str]
    priority: int  # Lower number = higher priority precedence
    description: str

    def matches(self, query: str) -> bool:
        normalized = query.lower()
        return any(re.search(rf"\b{re.escape(pattern.lower())}\b", normalized) for pattern in self.patterns)


# Documented rule priority table:
# 1. calculate (priority 1) -> specific operational computation has higher specificity
# 2. help      (priority 2) -> general informational assistance has lower specificity
DEFAULT_RULES: List[IntentRule] = [
    IntentRule(
        intent_name="calculate",
        handler_name="calculator",
        patterns=["calculate", "calc", "sum", "multiply", "divide", "add", "subtract", "math"],
        priority=1,
        description="Routes arithmetic and computational tasks to the calculator handler."
    ),
    IntentRule(
        intent_name="help",
        handler_name="support",
        patterns=["help", "support", "assist", "guide", "faq", "info"],
        priority=2,
        description="Routes general assistance and guidance queries to the support handler."
    ),
]


# ---------------------------------------------------------------------------
# Handlers (Component boundaries: Pure business logic functions)
# ---------------------------------------------------------------------------

def support_handler(request: ToolRequest) -> ToolResult:
    """Support tool handler: handles help, documentation, and user guidance."""
    return ToolResult(
        success=True,
        data={
            "handler": "support",
            "message": "Support guidance: available modules include documentation, FAQs, and system tutorials.",
            "query": request.query,
        }
    )


def calculator_handler(request: ToolRequest) -> ToolResult:
    """Calculator tool handler: handles mathematical operations."""
    # Local safe arithmetic evaluation fixture
    expr_match = re.search(r"(\d+(?:\.\d+)?)\s*([\+\-\*\/])\s*(\d+(?:\.\d+)?)", request.query)
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

    return ToolResult(
        success=True,
        data={
            "handler": "calculator",
            "result": computed if computed is not None else "Calculator ready for input",
            "query": request.query,
        }
    )


def fallback_handler(request: ToolRequest) -> ToolResult:
    """Fallback tool handler: handles unknown or unsupported requests."""
    return ToolResult(
        success=True,
        data={
            "handler": "fallback",
            "message": "Unrecognized intent. Available tools are 'support' and 'calculator'.",
            "query": request.query,
        }
    )


# ---------------------------------------------------------------------------
# Router: Decision Engine with Auditable Logging
# ---------------------------------------------------------------------------

class ToolRouter:
    """
    Routes requests using explicit intent rules, priority-based ambiguity resolution,
    and fallback handling while producing an auditable decision record.
    """

    def __init__(self, rules: Optional[List[IntentRule]] = None):
        self.rules = sorted(rules or DEFAULT_RULES, key=lambda r: r.priority)
        self.handlers: Dict[str, Callable[[ToolRequest], ToolResult]] = {
            "support": support_handler,
            "calculator": calculator_handler,
            "fallback": fallback_handler,
        }
        self.audit_log: List[AuditRecord] = []

    def register_handler(self, name: str, handler: Callable[[ToolRequest], ToolResult]) -> None:
        self.handlers[name] = handler

    def resolve_intent(self, query: str) -> tuple[List[str], str, str, str]:
        """
        Detects matches, resolves ambiguity using documented priority,
        and returns (matched_intents, selected_intent, resolution_rule, handler_name).
        """
        matched = [rule for rule in self.rules if rule.matches(query)]
        matched_intents = [rule.intent_name for rule in matched]

        if not matched:
            return (
                [],
                "unknown",
                "default_fallback: no explicit rules matched query",
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

        # Ambiguous case: multiple rules matched.
        # Rules are pre-sorted by priority ascending (1 is higher precedence than 2).
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
        """
        Dispatches request to appropriate handler and attaches audit record to metadata.
        """
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

        handler = self.handlers.get(handler_name, self.handlers["fallback"])
        result = handler(request)

        # Connect audit record to output metadata (Lab 06 ToolResult pattern)
        if result.metadata is None:
            result.metadata = {}
        result.metadata["audit"] = audit.to_dict()

        return result


# ---------------------------------------------------------------------------
# CLI / Local Demonstration Invocation
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
    print("Applied Lab R49-T021: Tool Routing and Auditable Decision Records Demo")
    print("=" * 80)
    for label, query in scenarios:
        req = ToolRequest(query=query)
        result = router.dispatch(req)
        audit = result.metadata["audit"]
        print(f"\n[{label}]")
        print(f"  Input Query:     '{req.query}'")
        print(f"  Matched Intents: {audit['matched_intents']}")
        print(f"  Selected Intent: {audit['selected_intent']}")
        print(f"  Handler Invoked: {audit['handler_name']}")
        print(f"  Resolution Rule: {audit['resolution_rule']}")
        print(f"  Handler Output:  {result.data}")


if __name__ == "__main__":
    run_demo()
