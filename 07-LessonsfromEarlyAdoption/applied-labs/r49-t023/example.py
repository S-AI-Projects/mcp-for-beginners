"""
Applied Lab R49-T023: Local JSON Tool Dispatch with Cross-Verification against Independent Calculation.

Lesson Context (07-LessonsfromEarlyAdoption/README.md):
Early adopters of MCP in production discovered that as tool dispatch systems grow,
middleware, type coercions, and wrappers can introduce subtle drift or regressions.
A proven lesson from early adoption is to validate tool implementations by comparing
the runtime dispatcher against an independent calculation or explicit expected-result table
using identical inputs.

Contract Requirements:
- Explicit allowlist: only 'add' and 'multiply' can execute.
- Strict numeric validation: 'a' and 'b' must be numbers (int or float; strictly reject bool/str).
- Expected operations: add(2, 3) -> 5; multiply(2, 3) -> 6.
- Structured errors: unknown tool and string 'a' are structured errors.
- Failure isolation: a failed call halts immediately and cannot execute another tool.
- Focus: Compare the direct implementation with a simpler independent calculation or
  explicit expected-result table using identical inputs.

Simplification Boundary:
This is a local contract fixture demonstrating tool validation and comparative verification.
It does not implement full async JSON-RPC networking or remote transport layers.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple, Union
import json


# ---------------------------------------------------------------------------
# Contracts & Error Envelopes
# ---------------------------------------------------------------------------

@dataclass
class ToolError:
    """Structured error envelope representing failed validation or execution."""
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
    """Standardized response envelope for tool execution."""
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


@dataclass
class ComparisonRecord:
    """Record comparing direct dispatcher output against independent calculation."""
    tool: str
    arguments: Dict[str, Any]
    dispatcher_success: bool
    dispatcher_result: Optional[Union[int, float]]
    reference_result: Optional[Union[int, float]]
    agrees: bool
    notes: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tool": self.tool,
            "arguments": self.arguments,
            "dispatcher_success": self.dispatcher_success,
            "dispatcher_result": self.dispatcher_result,
            "reference_result": self.reference_result,
            "agrees": self.agrees,
            "notes": self.notes
        }


# ---------------------------------------------------------------------------
# Tool Handlers (Direct Implementation)
# ---------------------------------------------------------------------------

class CalculatorTools:
    """Production-style tool handler class with explicit invocation tracking."""

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
# Independent Calculation Reference Oracle (Early Adopter Pattern)
# ---------------------------------------------------------------------------

def independent_reference_calculate(tool: str, a: Any, b: Any) -> Optional[Union[int, float]]:
    """
    Independent reference calculation oracle.
    Evaluates inputs using minimal, pure primitive operations, serving as the
    ground truth benchmark against which the dispatcher is compared.
    """
    if not (isinstance(a, (int, float)) and not isinstance(a, bool)):
        return None
    if not (isinstance(b, (int, float)) and not isinstance(b, bool)):
        return None

    if tool == "add":
        return a + b
    elif tool == "multiply":
        return a * b
    return None


# Explicit Expected-Result Table for Identical Inputs
EXPECTED_RESULT_TABLE: List[Dict[str, Any]] = [
    {"tool": "add", "arguments": {"a": 2, "b": 3}, "expected_result": 5},
    {"tool": "multiply", "arguments": {"a": 2, "b": 3}, "expected_result": 6},
    {"tool": "add", "arguments": {"a": 0, "b": 0}, "expected_result": 0},
    {"tool": "multiply", "arguments": {"a": 1, "b": 1}, "expected_result": 1},
    {"tool": "add", "arguments": {"a": -5, "b": 12}, "expected_result": 7},
    {"tool": "multiply", "arguments": {"a": 4, "b": 2.5}, "expected_result": 10.0},
]


# ---------------------------------------------------------------------------
# Tool Dispatcher with Strict Allowlist & Argument Validation
# ---------------------------------------------------------------------------

class LocalToolDispatcher:
    """
    Dispatches tool calls through an explicit allowlist and argument validation.
    Enforces that:
    1. Only 'add' and 'multiply' can execute.
    2. 'a' and 'b' must be numbers (bool and str strictly rejected).
    3. Failed call halts immediately and executes no handler.
    """

    ALLOWED_TOOLS: Set[str] = {"add", "multiply"}

    def __init__(self, tools: Optional[CalculatorTools] = None):
        self.tools = tools or CalculatorTools()
        self.history: List[ToolResponse] = []

    def _validate_numeric(self, param_name: str, value: Any) -> Optional[ToolError]:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return ToolError(
                code="INVALID_ARGUMENT",
                message=f"Argument '{param_name}' must be a numeric value (int or float), got {type(value).__name__}.",
                details={"param": param_name, "value": value, "type": type(value).__name__}
            )
        return None

    def dispatch(self, raw_call: Union[str, Dict[str, Any]]) -> ToolResponse:
        if isinstance(raw_call, str):
            try:
                call_data = json.loads(raw_call)
            except json.JSONDecodeError as err:
                resp = ToolResponse(
                    success=False,
                    tool=None,
                    error=ToolError(code="PARSE_ERROR", message=f"Malformed JSON: {err}")
                )
                self.history.append(resp)
                return resp
        elif isinstance(raw_call, dict):
            call_data = raw_call
        else:
            resp = ToolResponse(
                success=False,
                tool=None,
                error=ToolError(code="INVALID_REQUEST", message="Request must be a dictionary or JSON string.")
            )
            self.history.append(resp)
            return resp

        tool_name = call_data.get("tool")
        arguments = call_data.get("arguments")

        # 1. Allowlist verification
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
            self.history.append(resp)
            return resp

        # 2. Argument dictionary validation
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
            self.history.append(resp)
            return resp

        # 3. Required arguments check
        for param in ("a", "b"):
            if param not in arguments:
                resp = ToolResponse(
                    success=False,
                    tool=tool_name,
                    error=ToolError(
                        code="MISSING_ARGUMENT",
                        message=f"Missing required parameter '{param}'.",
                        details={"param": param}
                    )
                )
                self.history.append(resp)
                return resp

        # 4. Strict numeric validation
        err_a = self._validate_numeric("a", arguments["a"])
        if err_a:
            resp = ToolResponse(success=False, tool=tool_name, error=err_a)
            self.history.append(resp)
            return resp

        err_b = self._validate_numeric("b", arguments["b"])
        if err_b:
            resp = ToolResponse(success=False, tool=tool_name, error=err_b)
            self.history.append(resp)
            return resp

        # 5. Execute handler
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
            self.history.append(resp)
            return resp

        resp = ToolResponse(success=True, tool=tool_name, result=res)
        self.history.append(resp)
        return resp

    def dispatch_batch(self, calls: List[Dict[str, Any]], stop_on_failure: bool = True) -> List[ToolResponse]:
        """Dispatches multiple calls, halting immediately if a call fails."""
        results: List[ToolResponse] = []
        for call in calls:
            res = self.dispatch(call)
            results.append(res)
            if not res.success and stop_on_failure:
                break
        return results

    def compare_with_reference(self, call_data: Dict[str, Any]) -> ComparisonRecord:
        """
        Executes the call through the dispatcher and compares with the independent reference oracle.
        """
        tool = call_data.get("tool", "")
        args = call_data.get("arguments", {})
        resp = self.dispatch(call_data)

        ref_result = independent_reference_calculate(tool, args.get("a"), args.get("b"))
        agrees = (resp.success and resp.result == ref_result) or (not resp.success and ref_result is None)
        notes = "Results match perfectly" if agrees else "Discrepancy detected between dispatcher and reference"

        return ComparisonRecord(
            tool=tool,
            arguments=args,
            dispatcher_success=resp.success,
            dispatcher_result=resp.result,
            reference_result=ref_result,
            agrees=agrees,
            notes=notes
        )


# ---------------------------------------------------------------------------
# CLI / Demonstration
# ---------------------------------------------------------------------------

def run_demo() -> None:
    dispatcher = LocalToolDispatcher()

    print("=" * 80)
    print("Applied Lab R49-T023: Tool Dispatch with Independent Oracle Comparison")
    print("=" * 80)

    for entry in EXPECTED_RESULT_TABLE:
        call = {"tool": entry["tool"], "arguments": entry["arguments"]}
        cmp_rec = dispatcher.compare_with_reference(call)
        print(f"\n[Comparison for {entry['tool']}({entry['arguments']['a']}, {entry['arguments']['b']})]")
        print(f"  Dispatcher Result: {cmp_rec.dispatcher_result}")
        print(f"  Reference Result:  {cmp_rec.reference_result}")
        print(f"  Expected Result:   {entry['expected_result']}")
        print(f"  Agreed:            {cmp_rec.agrees} ({cmp_rec.notes})")

    # Negative / Failure scenarios
    failure_cases = [
        ("Unknown Tool", {"tool": "power", "arguments": {"a": 2, "b": 3}}),
        ("Invalid String 'a'", {"tool": "add", "arguments": {"a": "2", "b": 3}}),
    ]
    for label, call in failure_cases:
        resp = dispatcher.dispatch(call)
        print(f"\n[{label}]")
        print(f"  Output: {json.dumps(resp.to_dict(), indent=2)}")


if __name__ == "__main__":
    run_demo()
