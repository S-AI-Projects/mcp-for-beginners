"""
Applied Lab R49-T028: Tool Dispatch with Error Explanation and Next-Input Recovery in VS Code AI Chat.

Lesson Context (11-MCPServerHandsOnLabs/09-VS-Code/README.md):
In interactive VS Code AI Chat environments (e.g. GitHub Copilot invoking MCP tools),
the assistant may occasionally emit malformed JSON, omit required parameters, or pass
invalid string representations. An enterprise MCP server must:
1. Detect invalid or missing arguments without crashing or leaking unhandled exceptions.
2. Return a structured error envelope explaining the exact parameter deficiency.
3. Maintain clean server session state, ensuring full recovery on the immediate next valid input.
4. Guarantee that failed calls cannot execute any tool handlers.

Contract Requirements:
- Explicit allowlist: only 'add' and 'multiply' can execute.
- Strict numeric validation: 'a' and 'b' must be numbers (int or float; strictly reject bool and str).
- Expected operations: add(2, 3) -> 5; multiply(2, 3) -> 6.
- Structured errors: unknown tool and string 'a' are structured errors.
- Failure isolation: a failed call cannot execute another tool.
- Focus: Exercise a documented invalid/missing-data case, explain the error, and demonstrate
  recovery on the next valid input.

Simplification Boundary:
This is a local contract fixture demonstrating error explanation and session recovery.
It does not implement full async JSON-RPC networking or remote socket transports.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple, Union
import json


# ---------------------------------------------------------------------------
# Data Models and Error Envelopes
# ---------------------------------------------------------------------------

@dataclass
class ToolError:
    """Structured error envelope providing detailed diagnostic explanations."""
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
    """Standardized response envelope for VS Code tool execution."""
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
# Tool Handlers
# ---------------------------------------------------------------------------

class CalculatorTools:
    """Tool execution handlers with call count tracking."""

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
# Tool Dispatcher with Resilient Recovery
# ---------------------------------------------------------------------------

class VSCodeToolDispatcher:
    """
    Local tool dispatcher designed for interactive VS Code AI sessions.
    Provides clear error explanations and clean recovery on subsequent inputs.
    """

    ALLOWED_TOOLS: Set[str] = {"add", "multiply"}

    def __init__(self, tools: Optional[CalculatorTools] = None):
        self.tools = tools or CalculatorTools()
        self.session_history: List[ToolResponse] = []

    def _validate_numeric(self, param_name: str, value: Any) -> Optional[ToolError]:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return ToolError(
                code="INVALID_ARGUMENT",
                message=(
                    f"Argument '{param_name}' must be a numeric value (int or float), "
                    f"got {type(value).__name__}."
                ),
                details={
                    "parameter": param_name,
                    "received_value": value,
                    "received_type": type(value).__name__,
                    "expected_types": ["int", "float"],
                    "remediation": f"Pass a valid number for '{param_name}', e.g., 2 or 2.5."
                }
            )
        return None

    def dispatch(self, raw_call: Union[str, Dict[str, Any]]) -> ToolResponse:
        # Step 1: Parse Request
        if isinstance(raw_call, str):
            try:
                call_data = json.loads(raw_call)
            except json.JSONDecodeError as err:
                resp = ToolResponse(
                    success=False,
                    tool=None,
                    error=ToolError(code="PARSE_ERROR", message=f"Malformed JSON: {err}")
                )
                self.session_history.append(resp)
                return resp
        elif isinstance(raw_call, dict):
            call_data = raw_call
        else:
            resp = ToolResponse(
                success=False,
                tool=None,
                error=ToolError(code="INVALID_REQUEST", message="Request must be a dictionary or JSON string.")
            )
            self.session_history.append(resp)
            return resp

        tool_name = call_data.get("tool")
        arguments = call_data.get("arguments")

        # Step 2: Check Allowlist
        if tool_name not in self.ALLOWED_TOOLS:
            resp = ToolResponse(
                success=False,
                tool=tool_name,
                error=ToolError(
                    code="UNKNOWN_TOOL",
                    message=f"Tool '{tool_name}' is not in the allowlist. Allowed: {sorted(list(self.ALLOWED_TOOLS))}.",
                    details={"tool": tool_name, "allowed": sorted(list(self.ALLOWED_TOOLS))}
                )
            )
            self.session_history.append(resp)
            return resp

        # Step 3: Validate Argument Dictionary
        if not isinstance(arguments, dict):
            resp = ToolResponse(
                success=False,
                tool=tool_name,
                error=ToolError(
                    code="INVALID_ARGUMENTS_STRUCTURE",
                    message="The 'arguments' payload must be a dictionary.",
                    details={"tool": tool_name}
                )
            )
            self.session_history.append(resp)
            return resp

        # Step 4: Check Missing Data
        for param in ("a", "b"):
            if param not in arguments:
                resp = ToolResponse(
                    success=False,
                    tool=tool_name,
                    error=ToolError(
                        code="MISSING_ARGUMENT",
                        message=f"Missing required numeric parameter '{param}'.",
                        details={
                            "missing_parameter": param,
                            "required_parameters": ["a", "b"],
                            "provided_arguments": list(arguments.keys()),
                            "remediation": f"Ensure '{param}' is included in arguments, e.g., {{'a': 2, 'b': 3}}."
                        }
                    )
                )
                self.session_history.append(resp)
                return resp

        # Step 5: Check Numeric Types
        err_a = self._validate_numeric("a", arguments["a"])
        if err_a:
            resp = ToolResponse(success=False, tool=tool_name, error=err_a)
            self.session_history.append(resp)
            return resp

        err_b = self._validate_numeric("b", arguments["b"])
        if err_b:
            resp = ToolResponse(success=False, tool=tool_name, error=err_b)
            self.session_history.append(resp)
            return resp

        # Step 6: Execute Handler
        if tool_name == "add":
            res = self.tools.add(arguments["a"], arguments["b"])
        elif tool_name == "multiply":
            res = self.tools.multiply(arguments["a"], arguments["b"])
        else:
            resp = ToolResponse(
                success=False,
                tool=tool_name,
                error=ToolError(code="UNKNOWN_TOOL", message=f"Unmapped tool '{tool_name}'.")
            )
            self.session_history.append(resp)
            return resp

        resp = ToolResponse(success=True, tool=tool_name, result=res)
        self.session_history.append(resp)
        return resp

    def dispatch_batch(self, calls: List[Dict[str, Any]], stop_on_failure: bool = True) -> List[ToolResponse]:
        results: List[ToolResponse] = []
        for call in calls:
            res = self.dispatch(call)
            results.append(res)
            if not res.success and stop_on_failure:
                break
        return results


# ---------------------------------------------------------------------------
# Interactive Error & Recovery Demonstration (Focus of Lab)
# ---------------------------------------------------------------------------

def run_recovery_demonstration() -> List[Dict[str, Any]]:
    """
    Demonstrates error explanation and recovery across conversational turns:
    Turn 1: Missing data (missing parameter 'b') -> Error explaining omission
    Turn 2: Client provides corrected arguments -> Full recovery (result: 5)
    Turn 3: Invalid type (string 'a' instead of number) -> Error explaining type
    Turn 4: Client provides corrected arguments -> Full recovery (result: 6)
    """
    dispatcher = VSCodeToolDispatcher()

    turns = [
        {
            "turn": 1,
            "description": "Turn 1 (Fault): Missing required parameter 'b'",
            "call": {"tool": "add", "arguments": {"a": 2}},
        },
        {
            "turn": 2,
            "description": "Turn 2 (Recovery): Client supplies corrected valid payload",
            "call": {"tool": "add", "arguments": {"a": 2, "b": 3}},
        },
        {
            "turn": 3,
            "description": "Turn 3 (Fault): String argument 'a'",
            "call": {"tool": "multiply", "arguments": {"a": "2", "b": 3}},
        },
        {
            "turn": 4,
            "description": "Turn 4 (Recovery): Client supplies corrected valid payload",
            "call": {"tool": "multiply", "arguments": {"a": 2, "b": 3}},
        },
    ]

    history = []
    for turn in turns:
        resp = dispatcher.dispatch(turn["call"])
        history.append({
            "turn": turn["turn"],
            "description": turn["description"],
            "call": turn["call"],
            "response": resp.to_dict(),
            "status": "SUCCESS" if resp.success else "REJECTED_WITH_EXPLANATION"
        })
    return history


def run_demo() -> None:
    print("=" * 80)
    print("Applied Lab R49-T028: VS Code Error Explanation & Next-Input Recovery Demo")
    print("=" * 80)
    history = run_recovery_demonstration()
    for item in history:
        print(f"\n[{item['description']}]")
        print(f"  Call:     {item['call']}")
        print(f"  Response: {json.dumps(item['response'], indent=2)}")


if __name__ == "__main__":
    run_demo()
