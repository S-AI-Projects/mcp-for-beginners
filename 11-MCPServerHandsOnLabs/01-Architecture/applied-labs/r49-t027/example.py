"""
Applied Lab R49-T027: Capability Negotiation, Set Intersection, and Feature Gating.

Lesson Context (11-MCPServerHandsOnLabs/01-Architecture/README.md):
In MCP protocol architecture (Layer 1: Protocol Layer), during initial session initialization,
the client and server advertise their supported capabilities (such as tools, resources, prompts).
The active session capabilities are determined strictly by set intersection:
    Negotiated Capabilities = Client Capabilities ∩ Server Capabilities

If a client attempts to invoke an unnegotiated capability (for example, attempting to call
'resources' when only 'tools' was negotiated), the protocol layer must reject the request
immediately before dispatching to any backend handler.

Contract Requirements:
- Client capabilities: {'tools', 'resources'}
- Server capabilities: {'tools', 'prompts'}
- Handshake negotiation: yields intersection {'tools'}
- Calling 'resources' is rejected before dispatch with a structured error.
- Valid tool calls: add(2, 3) -> 5, multiply(2, 3) -> 6.
- Focus: Publish a worked input-to-output explanation and execute the exact example as a regression test.

Simplification Boundary:
This is a local contract fixture demonstrating capability intersection and pre-dispatch gating.
It does not implement full async JSON-RPC networking or remote socket transports.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Union
import json


# ---------------------------------------------------------------------------
# Data Models and Error Envelopes
# ---------------------------------------------------------------------------

@dataclass
class ToolError:
    """Structured error envelope for capability gating or execution failures."""
    code: str
    message: str
    details: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "code": self.code,
            "message": self.message,
            "details": self.details or {}
        }


@dataclass
class InvocationResponse:
    """Standardized response contract for MCP capability invocations."""
    success: bool
    capability: str
    target: Optional[str]
    result: Optional[Any] = None
    error: Optional[ToolError] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "capability": self.capability,
            "target": self.target,
            "result": self.result,
            "error": self.error.to_dict() if self.error else None
        }


# ---------------------------------------------------------------------------
# Handlers and Resource Provider (Backends)
# ---------------------------------------------------------------------------

class MockResourceProvider:
    """Simulated backend resource provider (should never be called if unnegotiated)."""
    def __init__(self):
        self.call_count = 0

    def read_resource(self, uri: str) -> Dict[str, Any]:
        self.call_count += 1
        return {"uri": uri, "content": "mock_resource_data"}


class MockToolExecutor:
    """Tool execution handlers."""
    def __init__(self):
        self.add_call_count = 0
        self.multiply_call_count = 0

    def add(self, a: Union[int, float], b: Union[int, float]) -> Union[int, float]:
        self.add_call_count += 1
        return a + b

    def multiply(self, a: Union[int, float], b: Union[int, float]) -> Union[int, float]:
        self.multiply_call_count += 1
        return a * b


# ---------------------------------------------------------------------------
# Capability Session & Pre-Dispatch Gating Engine
# ---------------------------------------------------------------------------

class MCPSession:
    """
    Manages client-server capability negotiation and pre-dispatch gating.
    """

    ALLOWED_TOOLS: Set[str] = {"add", "multiply"}

    def __init__(
        self,
        client_capabilities: Set[str],
        server_capabilities: Set[str],
        tools: Optional[MockToolExecutor] = None,
        resources: Optional[MockResourceProvider] = None
    ):
        self.client_capabilities = set(client_capabilities)
        self.server_capabilities = set(server_capabilities)
        # Capability negotiation via set intersection
        self.negotiated_capabilities: Set[str] = self.client_capabilities.intersection(self.server_capabilities)

        self.tools = tools or MockToolExecutor()
        self.resources = resources or MockResourceProvider()

    def invoke(self, request: Dict[str, Any]) -> InvocationResponse:
        """
        Processes an incoming invocation with pre-dispatch capability gating.
        """
        capability = request.get("capability")

        # 1. Feature Gating: Capability Pre-Dispatch Check
        if capability not in self.negotiated_capabilities:
            return InvocationResponse(
                success=False,
                capability=str(capability),
                target=request.get("target"),
                error=ToolError(
                    code="UNNEGOTIATED_CAPABILITY",
                    message=(
                        f"Capability '{capability}' was not negotiated for this session. "
                        f"Negotiated capabilities: {sorted(list(self.negotiated_capabilities))}."
                    ),
                    details={
                        "requested_capability": capability,
                        "client_capabilities": sorted(list(self.client_capabilities)),
                        "server_capabilities": sorted(list(self.server_capabilities)),
                        "negotiated_capabilities": sorted(list(self.negotiated_capabilities)),
                    }
                )
            )

        # 2. Dispatch to Negotiated Capability
        if capability == "tools":
            return self._dispatch_tool(request)
        elif capability == "resources":
            uri = request.get("target", "")
            data = self.resources.read_resource(uri)
            return InvocationResponse(success=True, capability="resources", target=uri, result=data)
        elif capability == "prompts":
            prompt_name = request.get("target", "")
            return InvocationResponse(
                success=True,
                capability="prompts",
                target=prompt_name,
                result={"prompt": prompt_name, "template": "Sample prompt template"}
            )
        else:
            return InvocationResponse(
                success=False,
                capability=capability,
                target=request.get("target"),
                error=ToolError(code="UNKNOWN_CAPABILITY_HANDLER", message=f"No handler for capability '{capability}'.")
            )

    def _dispatch_tool(self, request: Dict[str, Any]) -> InvocationResponse:
        tool_name = request.get("target")
        arguments = request.get("arguments")

        if tool_name not in self.ALLOWED_TOOLS:
            return InvocationResponse(
                success=False,
                capability="tools",
                target=tool_name,
                error=ToolError(
                    code="UNKNOWN_TOOL",
                    message=f"Tool '{tool_name}' is not in the allowlist. Allowed: {sorted(list(self.ALLOWED_TOOLS))}.",
                    details={"tool": tool_name}
                )
            )

        if not isinstance(arguments, dict):
            return InvocationResponse(
                success=False,
                capability="tools",
                target=tool_name,
                error=ToolError(code="INVALID_ARGUMENTS_STRUCTURE", message="Arguments must be a dictionary.")
            )

        for param in ("a", "b"):
            if param not in arguments:
                return InvocationResponse(
                    success=False,
                    capability="tools",
                    target=tool_name,
                    error=ToolError(code="MISSING_ARGUMENT", message=f"Missing required parameter '{param}'.")
                )
            val = arguments[param]
            if isinstance(val, bool) or not isinstance(val, (int, float)):
                return InvocationResponse(
                    success=False,
                    capability="tools",
                    target=tool_name,
                    error=ToolError(
                        code="INVALID_ARGUMENT",
                        message=f"Argument '{param}' must be a numeric value (int or float), got {type(val).__name__}."
                    )
                )

        if tool_name == "add":
            res = self.tools.add(arguments["a"], arguments["b"])
        elif tool_name == "multiply":
            res = self.tools.multiply(arguments["a"], arguments["b"])
        else:
            return InvocationResponse(
                success=False,
                capability="tools",
                target=tool_name,
                error=ToolError(code="UNKNOWN_TOOL", message=f"Unmapped tool '{tool_name}'.")
            )

        return InvocationResponse(success=True, capability="tools", target=tool_name, result=res)


# ---------------------------------------------------------------------------
# Worked Input-to-Output Explanation Generator & CLI Demo
# ---------------------------------------------------------------------------

def run_worked_explanation() -> Dict[str, Any]:
    """
    Executes the exact worked input-to-output scenario for regression testing:
    - Client: {'tools', 'resources'}
    - Server: {'tools', 'prompts'}
    - Negotiated: {'tools'}
    - Invocation A: capability='tools', target='add', arguments={'a': 2, 'b': 3} -> 5
    - Invocation B: capability='tools', target='multiply', arguments={'a': 2, 'b': 3} -> 6
    - Invocation C: capability='resources', target='schema://retail' -> Rejected before dispatch
    """
    client_caps = {"tools", "resources"}
    server_caps = {"tools", "prompts"}

    session = MCPSession(client_capabilities=client_caps, server_capabilities=server_caps)

    # 1. Valid tool calls
    call_add = {"capability": "tools", "target": "add", "arguments": {"a": 2, "b": 3}}
    resp_add = session.invoke(call_add)

    call_mult = {"capability": "tools", "target": "multiply", "arguments": {"a": 2, "b": 3}}
    resp_mult = session.invoke(call_mult)

    # 2. Rejected unnegotiated capability call
    call_res = {"capability": "resources", "target": "schema://retail"}
    resp_res = session.invoke(call_res)

    explanation = {
        "client_capabilities": sorted(list(client_caps)),
        "server_capabilities": sorted(list(server_caps)),
        "negotiated_capabilities": sorted(list(session.negotiated_capabilities)),
        "invocations": [
            {"request": call_add, "response": resp_add.to_dict(), "action": "ACCEPTED_AND_DISPATCHED"},
            {"request": call_mult, "response": resp_mult.to_dict(), "action": "ACCEPTED_AND_DISPATCHED"},
            {"request": call_res, "response": resp_res.to_dict(), "action": "REJECTED_BEFORE_DISPATCH"},
        ],
        "backend_resource_provider_call_count": session.resources.call_count
    }
    return explanation


def run_demo() -> None:
    exp = run_worked_explanation()
    print("=" * 80)
    print("Applied Lab R49-T027: Capability Negotiation & Pre-Dispatch Gating Demo")
    print("=" * 80)
    print(f"Client Capabilities:     {exp['client_capabilities']}")
    print(f"Server Capabilities:     {exp['server_capabilities']}")
    print(f"Negotiated Intersection: {exp['negotiated_capabilities']}")
    print("\nWorked Invocations:")
    for item in exp["invocations"]:
        print(f"\n[{item['action']}]")
        print(f"  Request:  {item['request']}")
        print(f"  Response: {json.dumps(item['response'], indent=2)}")
    print(f"\nResource Handler Invocations: {exp['backend_resource_provider_call_count']} (Expected: 0)")


if __name__ == "__main__":
    run_demo()
