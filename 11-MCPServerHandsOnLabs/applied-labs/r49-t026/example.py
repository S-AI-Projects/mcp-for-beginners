"""
Applied Lab R49-T026: Tool Dispatch Refactoring with Responsibility Extraction and Equivalence Proof.

Lesson Context (11-MCPServerHandsOnLabs/README.md):
In building modular, enterprise-grade MCP servers (such as database query and analytics tools),
monolithic handlers quickly become unmaintainable and difficult to secure. A fundamental
software design principle in MCP server development is extracting distinct named responsibilities
(such as parameter schema validation) from dispatch orchestration, while preserving strict
contract equivalence.

Contract Requirements:
- Explicit allowlist: only 'add' and 'multiply' can execute.
- Strict numeric validation: 'a' and 'b' must be numbers (int or float; strictly reject bool and str).
- Expected operations: add(2, 3) -> 5; multiply(2, 3) -> 6.
- Structured errors: unknown tool and string 'a' are structured errors.
- Failure isolation: a failed call halts immediately and cannot execute another tool.
- Focus: Implement a correct baseline, then extract one named responsibility ('ArgumentValidator').
  Keep the same contract and prove before/after equivalence on the fixture.

Simplification Boundary:
This is a local contract fixture demonstrating architectural refactoring and equivalence proof.
It does not implement full async networking or remote MCP transports.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple, Union
import json


# ---------------------------------------------------------------------------
# Data Contracts & Error Envelopes
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
    """Standardized response contract for tool execution."""
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


class CalculatorTools:
    """Execution handlers with invocation tracking."""
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
# 1. Baseline Implementation (Monolithic Dispatcher)
# ---------------------------------------------------------------------------

class BaselineToolDispatcher:
    """
    Baseline implementation where tool routing, schema validation, and execution
    are coupled together in a single monolithic dispatch method.
    """

    ALLOWED_TOOLS: Set[str] = {"add", "multiply"}

    def __init__(self, tools: Optional[CalculatorTools] = None):
        self.tools = tools or CalculatorTools()

    def dispatch(self, raw_call: Union[str, Dict[str, Any]]) -> ToolResponse:
        # Parse JSON
        if isinstance(raw_call, str):
            try:
                call_data = json.loads(raw_call)
            except json.JSONDecodeError as err:
                return ToolResponse(
                    success=False,
                    tool=None,
                    error=ToolError(code="PARSE_ERROR", message=f"Malformed JSON: {err}")
                )
        elif isinstance(raw_call, dict):
            call_data = raw_call
        else:
            return ToolResponse(
                success=False,
                tool=None,
                error=ToolError(code="INVALID_REQUEST", message="Request must be a dictionary or JSON string.")
            )

        tool_name = call_data.get("tool")
        arguments = call_data.get("arguments")

        # Monolithic Step 1: Allowlist check
        if tool_name not in self.ALLOWED_TOOLS:
            return ToolResponse(
                success=False,
                tool=tool_name,
                error=ToolError(
                    code="UNKNOWN_TOOL",
                    message=f"Tool '{tool_name}' is not in the allowlist. Allowed: {sorted(list(self.ALLOWED_TOOLS))}.",
                    details={"tool": tool_name}
                )
            )

        # Monolithic Step 2: Inlined argument structure check
        if not isinstance(arguments, dict):
            return ToolResponse(
                success=False,
                tool=tool_name,
                error=ToolError(
                    code="INVALID_ARGUMENTS_STRUCTURE",
                    message="The 'arguments' payload must be a dictionary.",
                    details={"tool": tool_name}
                )
            )

        # Monolithic Step 3: Inlined required parameter check
        for param in ("a", "b"):
            if param not in arguments:
                return ToolResponse(
                    success=False,
                    tool=tool_name,
                    error=ToolError(
                        code="MISSING_ARGUMENT",
                        message=f"Missing required parameter '{param}'.",
                        details={"param": param}
                    )
                )

        # Monolithic Step 4: Inlined numeric type check
        for param in ("a", "b"):
            val = arguments[param]
            if isinstance(val, bool) or not isinstance(val, (int, float)):
                return ToolResponse(
                    success=False,
                    tool=tool_name,
                    error=ToolError(
                        code="INVALID_ARGUMENT",
                        message=f"Argument '{param}' must be a numeric value (int or float), got {type(val).__name__}.",
                        details={"param": param, "value": val, "type": type(val).__name__}
                    )
                )

        # Monolithic Step 5: Execution
        if tool_name == "add":
            res = self.tools.add(arguments["a"], arguments["b"])
        elif tool_name == "multiply":
            res = self.tools.multiply(arguments["a"], arguments["b"])
        else:
            return ToolResponse(
                success=False,
                tool=tool_name,
                error=ToolError(code="UNKNOWN_TOOL", message=f"Unmapped tool '{tool_name}'.")
            )

        return ToolResponse(success=True, tool=tool_name, result=res)

    def dispatch_batch(self, calls: List[Dict[str, Any]], stop_on_failure: bool = True) -> List[ToolResponse]:
        results: List[ToolResponse] = []
        for call in calls:
            res = self.dispatch(call)
            results.append(res)
            if not res.success and stop_on_failure:
                break
        return results


# ---------------------------------------------------------------------------
# 2. Extracted Named Responsibility: NumericArgumentValidator
# ---------------------------------------------------------------------------

class NumericArgumentValidator:
    """
    Extracted named responsibility: Dedicated validator for tool arguments.
    Encapsulates parameter structure, required key presence, and strict numeric type rules.
    """

    @staticmethod
    def validate(tool_name: str, arguments: Any) -> Optional[ToolError]:
        if not isinstance(arguments, dict):
            return ToolError(
                code="INVALID_ARGUMENTS_STRUCTURE",
                message="The 'arguments' payload must be a dictionary.",
                details={"tool": tool_name}
            )

        for param in ("a", "b"):
            if param not in arguments:
                return ToolError(
                    code="MISSING_ARGUMENT",
                    message=f"Missing required parameter '{param}'.",
                    details={"param": param}
                )

        for param in ("a", "b"):
            val = arguments[param]
            if isinstance(val, bool) or not isinstance(val, (int, float)):
                return ToolError(
                    code="INVALID_ARGUMENT",
                    message=f"Argument '{param}' must be a numeric value (int or float), got {type(val).__name__}.",
                    details={"param": param, "value": val, "type": type(val).__name__}
                )

        return None


# ---------------------------------------------------------------------------
# 3. Refactored Implementation (Modular Tool Dispatcher)
# ---------------------------------------------------------------------------

class RefactoredToolDispatcher:
    """
    Refactored modular dispatcher that delegates argument validation to the
    extracted NumericArgumentValidator, maintaining the exact same contract.
    """

    ALLOWED_TOOLS: Set[str] = {"add", "multiply"}

    def __init__(
        self,
        tools: Optional[CalculatorTools] = None,
        validator: Optional[NumericArgumentValidator] = None
    ):
        self.tools = tools or CalculatorTools()
        self.validator = validator or NumericArgumentValidator()

    def dispatch(self, raw_call: Union[str, Dict[str, Any]]) -> ToolResponse:
        if isinstance(raw_call, str):
            try:
                call_data = json.loads(raw_call)
            except json.JSONDecodeError as err:
                return ToolResponse(
                    success=False,
                    tool=None,
                    error=ToolError(code="PARSE_ERROR", message=f"Malformed JSON: {err}")
                )
        elif isinstance(raw_call, dict):
            call_data = raw_call
        else:
            return ToolResponse(
                success=False,
                tool=None,
                error=ToolError(code="INVALID_REQUEST", message="Request must be a dictionary or JSON string.")
            )

        tool_name = call_data.get("tool")
        arguments = call_data.get("arguments")

        # Allowlist check
        if tool_name not in self.ALLOWED_TOOLS:
            return ToolResponse(
                success=False,
                tool=tool_name,
                error=ToolError(
                    code="UNKNOWN_TOOL",
                    message=f"Tool '{tool_name}' is not in the allowlist. Allowed: {sorted(list(self.ALLOWED_TOOLS))}.",
                    details={"tool": tool_name}
                )
            )

        # Delegated validation to extracted responsibility
        validation_error = self.validator.validate(tool_name, arguments)
        if validation_error:
            return ToolResponse(success=False, tool=tool_name, error=validation_error)

        # Execution
        if tool_name == "add":
            res = self.tools.add(arguments["a"], arguments["b"])
        elif tool_name == "multiply":
            res = self.tools.multiply(arguments["a"], arguments["b"])
        else:
            return ToolResponse(
                success=False,
                tool=tool_name,
                error=ToolError(code="UNKNOWN_TOOL", message=f"Unmapped tool '{tool_name}'.")
            )

        return ToolResponse(success=True, tool=tool_name, result=res)

    def dispatch_batch(self, calls: List[Dict[str, Any]], stop_on_failure: bool = True) -> List[ToolResponse]:
        results: List[ToolResponse] = []
        for call in calls:
            res = self.dispatch(call)
            results.append(res)
            if not res.success and stop_on_failure:
                break
        return results


# ---------------------------------------------------------------------------
# Equivalence Prover Function
# ---------------------------------------------------------------------------

def prove_before_after_equivalence(
    fixtures: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Executes each fixture through BOTH BaselineToolDispatcher and RefactoredToolDispatcher
    and asserts 100% equivalence of the response envelopes.
    """
    baseline_dispatcher = BaselineToolDispatcher()
    refactored_dispatcher = RefactoredToolDispatcher()

    audit_records = []
    for fixture in fixtures:
        call = fixture["call"]
        baseline_out = baseline_dispatcher.dispatch(call).to_dict()
        refactored_out = refactored_dispatcher.dispatch(call).to_dict()

        if baseline_out != refactored_out:
            raise AssertionError(
                f"Equivalence violation for call {call}:\n"
                f"Baseline:   {baseline_out}\n"
                f"Refactored: {refactored_out}"
            )

        audit_records.append({
            "fixture_id": fixture.get("id"),
            "call": call,
            "equivalent": True,
            "baseline_output": baseline_out,
            "refactored_output": refactored_out
        })

    return audit_records


# ---------------------------------------------------------------------------
# CLI / Demonstration
# ---------------------------------------------------------------------------

SAMPLE_FIXTURES: List[Dict[str, Any]] = [
    {"id": "add_normal", "call": {"tool": "add", "arguments": {"a": 2, "b": 3}}},
    {"id": "multiply_normal", "call": {"tool": "multiply", "arguments": {"a": 2, "b": 3}}},
    {"id": "boundary_zero", "call": {"tool": "add", "arguments": {"a": 0, "b": 0}}},
    {"id": "boundary_one", "call": {"tool": "multiply", "arguments": {"a": 1, "b": 1}}},
    {"id": "invalid_unknown_tool", "call": {"tool": "power", "arguments": {"a": 2, "b": 3}}},
    {"id": "invalid_string_a", "call": {"tool": "add", "arguments": {"a": "2", "b": 3}}},
    {"id": "invalid_bool_a", "call": {"tool": "multiply", "arguments": {"a": True, "b": 5}}},
    {"id": "missing_b", "call": {"tool": "add", "arguments": {"a": 10}}},
]

def run_demo() -> None:
    print("=" * 80)
    print("Applied Lab R49-T026: Baseline vs. Refactored Equivalence Demonstration")
    print("=" * 80)
    results = prove_before_after_equivalence(SAMPLE_FIXTURES)
    for res in results:
        print(f"\n[Fixture: {res['fixture_id']}]")
        print(f"  Call:        {res['call']}")
        print(f"  Baseline:    {res['baseline_output']}")
        print(f"  Refactored:  {res['refactored_output']}")
        print(f"  Equivalent:  {res['equivalent']}")
    print("\n" + "=" * 80)
    print("Equivalence successfully proved across all fixtures!")
    print("=" * 80)


if __name__ == "__main__":
    run_demo()
