"""
Applied Lab R49-T022: Local JSON Tool Dispatch with Allowlist and Numeric Validation.

Lesson Context (03-GettingStarted/README.md):
In MCP fundamentals, servers expose tools with explicit names and input schemas.
Clients send structured JSON requests to execute specific tools. Before executing
any tool handler, the server must:
1. Verify the tool name against an explicit allowlist (preventing arbitrary/unauthorized dispatch).
2. Validate parameter types and presence against the tool schema (strict numeric checks).
3. Halt execution immediately on error (a failed call cannot execute another tool).
4. Return a standardized response or structured error envelope.

Simplification Boundary:
This module is a local contract fixture demonstrating dispatch and schema validation.
It does not implement full JSON-RPC over stdio/HTTP transports, networking, or async IPC.
All state and execution tracking are local and deterministic.
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Set, Union
import json


# ---------------------------------------------------------------------------
# Public Data Contracts & Error Envelopes
# ---------------------------------------------------------------------------

@dataclass
class ToolError:
    """Structured error envelope aligned with MCP/JSON-RPC error principles."""
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
class ToolResponse:
    """Standardized response contract for tool dispatch."""
    success: bool
    tool: Optional[str]
    result: Optional[Union[int, float]] = None
    error: Optional[ToolError] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "tool": self.tool,
            "result": self.result,
            "error": self.error.to_dict() if self.error else None
        }


# ---------------------------------------------------------------------------
# Tool Handlers (Pure execution units with invocation tracking)
# ---------------------------------------------------------------------------

class CalculatorTools:
    """Tool implementations with explicit call counters to verify isolation."""
    
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
# Tool Dispatcher with Strict Allowlist & Argument Validation
# ---------------------------------------------------------------------------

class LocalToolDispatcher:
    """
    Dispatches tool calls through an explicit allowlist with strict numeric validation.
    Guarantees:
    - Only allowlisted tools ('add', 'multiply') can execute.
    - Arguments 'a' and 'b' must be real numeric values (int or float, strictly excluding bool).
    - On failure, execution aborts immediately; no other tool can execute.
    """

    ALLOWED_TOOLS: Set[str] = {"add", "multiply"}

    def __init__(self, tools: Optional[CalculatorTools] = None):
        self.tools = tools or CalculatorTools()
        self.dispatch_log: List[Dict[str, Any]] = []

    def _validate_numeric(self, param_name: str, value: Any) -> Optional[ToolError]:
        """
        Validates that a parameter is an integer or float.
        Boundary Decision:
        In Python, `bool` is a subclass of `int` (`isinstance(True, int) == True`).
        However, in strict tool contracts, booleans are not valid numbers.
        Therefore, booleans are explicitly rejected.
        """
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return ToolError(
                code="INVALID_ARGUMENT",
                message=f"Argument '{param_name}' must be a numeric value (int or float), got {type(value).__name__}.",
                details={"parameter": param_name, "received_value": value, "received_type": type(value).__name__}
            )
        return None

    def dispatch(self, raw_call: Union[str, Dict[str, Any]]) -> ToolResponse:
        """
        Dispatches a local JSON or dictionary tool call.
        Enforces:
        1. Tool allowlist check.
        2. Parameter presence and numeric type validation.
        3. Fails fast without invoking any handler if checks fail.
        """
        # Parse JSON if passed as string
        if isinstance(raw_call, str):
            try:
                call_data = json.loads(raw_call)
            except json.JSONDecodeError as err:
                response = ToolResponse(
                    success=False,
                    tool=None,
                    error=ToolError(code="PARSE_ERROR", message=f"Invalid JSON string: {err}")
                )
                self.dispatch_log.append(response.to_dict())
                return response
        elif isinstance(raw_call, dict):
            call_data = raw_call
        else:
            response = ToolResponse(
                success=False,
                tool=None,
                error=ToolError(code="INVALID_REQUEST", message="Request must be a dictionary or JSON string.")
            )
            self.dispatch_log.append(response.to_dict())
            return response

        tool_name = call_data.get("tool")
        arguments = call_data.get("arguments")

        # 1. Allowlist Validation
        if tool_name not in self.ALLOWED_TOOLS:
            response = ToolResponse(
                success=False,
                tool=tool_name,
                error=ToolError(
                    code="UNKNOWN_TOOL",
                    message=f"Tool '{tool_name}' is not in the allowlist. Allowed tools: {sorted(list(self.ALLOWED_TOOLS))}.",
                    details={"requested_tool": tool_name, "allowed_tools": sorted(list(self.ALLOWED_TOOLS))}
                )
            )
            self.dispatch_log.append(response.to_dict())
            return response

        # 2. Argument dictionary check
        if not isinstance(arguments, dict):
            response = ToolResponse(
                success=False,
                tool=tool_name,
                error=ToolError(
                    code="INVALID_ARGUMENTS_STRUCTURE",
                    message="The 'arguments' field must be a key-value dictionary.",
                    details={"tool": tool_name}
                )
            )
            self.dispatch_log.append(response.to_dict())
            return response

        # 3. Required parameters check
        for required_param in ("a", "b"):
            if required_param not in arguments:
                response = ToolResponse(
                    success=False,
                    tool=tool_name,
                    error=ToolError(
                        code="MISSING_ARGUMENT",
                        message=f"Missing required numeric argument '{required_param}'.",
                        details={"tool": tool_name, "missing": required_param}
                    )
                )
                self.dispatch_log.append(response.to_dict())
                return response

        a_val = arguments["a"]
        b_val = arguments["b"]

        # 4. Strict Numeric Type Validation (String a or b is a structured error)
        err_a = self._validate_numeric("a", a_val)
        if err_a:
            response = ToolResponse(success=False, tool=tool_name, error=err_a)
            self.dispatch_log.append(response.to_dict())
            return response

        err_b = self._validate_numeric("b", b_val)
        if err_b:
            response = ToolResponse(success=False, tool=tool_name, error=err_b)
            self.dispatch_log.append(response.to_dict())
            return response

        # 5. Handler Execution
        if tool_name == "add":
            calc_result = self.tools.add(a_val, b_val)
        elif tool_name == "multiply":
            calc_result = self.tools.multiply(a_val, b_val)
        else:
            # Defensive guard: unreachable due to allowlist, but ensures complete coverage
            response = ToolResponse(
                success=False,
                tool=tool_name,
                error=ToolError(code="UNKNOWN_TOOL", message=f"Unmapped tool: {tool_name}")
            )
            self.dispatch_log.append(response.to_dict())
            return response

        response = ToolResponse(
            success=True,
            tool=tool_name,
            result=calc_result
        )
        self.dispatch_log.append(response.to_dict())
        return response

    def dispatch_batch(self, calls: List[Dict[str, Any]], stop_on_failure: bool = True) -> List[ToolResponse]:
        """
        Dispatches a series of tool calls.
        When stop_on_failure is True, a failed call halts processing immediately,
        guaranteeing that a failed call cannot execute another tool.
        """
        results: List[ToolResponse] = []
        for call in calls:
            res = self.dispatch(call)
            results.append(res)
            if not res.success and stop_on_failure:
                break
        return results


# ---------------------------------------------------------------------------
# CLI / Local Demonstration Invocation
# ---------------------------------------------------------------------------

def run_demo() -> None:
    dispatcher = LocalToolDispatcher()

    fixtures = [
        ("Valid add(2, 3)", {"tool": "add", "arguments": {"a": 2, "b": 3}}),
        ("Valid multiply(2, 3)", {"tool": "multiply", "arguments": {"a": 2, "b": 3}}),
        ("Boundary smallest valid add(0, 0)", {"tool": "add", "arguments": {"a": 0, "b": 0}}),
        ("Boundary smallest valid multiply(1, 1)", {"tool": "multiply", "arguments": {"a": 1, "b": 1}}),
        ("Invalid String 'a'", {"tool": "add", "arguments": {"a": "2", "b": 3}}),
        ("Invalid Boolean 'a' (boundary)", {"tool": "multiply", "arguments": {"a": True, "b": 5}}),
        ("Invalid Unknown Tool", {"tool": "divide", "arguments": {"a": 10, "b": 2}}),
    ]

    print("=" * 80)
    print("Applied Lab R49-T022: Local JSON Tool Dispatch Demonstration")
    print("=" * 80)
    for label, payload in fixtures:
        resp = dispatcher.dispatch(payload)
        print(f"\n[{label}]")
        print(f"  Input:  {json.dumps(payload)}")
        print(f"  Output: {json.dumps(resp.to_dict(), indent=2)}")


if __name__ == "__main__":
    run_demo()
