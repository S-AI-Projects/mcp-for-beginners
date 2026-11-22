"""
Applied Lab R49-T024: Tool Dispatch with Intermediate State Recording and Invariant Verification.

Lesson Context (09-CaseStudy/README.md):
In real-world enterprise MCP deployments (such as automated workflow agents, APIM integrations,
and auditing systems), operations must be traceable, deterministic, and verifiable.
A critical architectural pattern is maintaining an audit trace of intermediate states
after each dispatch step and enforcing invariants that link these intermediate states
to the final output envelope.

Contract Requirements:
- Explicit allowlist: only 'add' and 'multiply' can execute.
- Strict numeric validation: 'a' and 'b' must be numbers (int or float; strictly reject bool and str).
- Expected operations: add(2, 3) -> 5; multiply(2, 3) -> 6.
- Structured errors: unknown tool and string 'a' are structured errors.
- Failure isolation: a failed call cannot execute another tool.
- Focus: Record the intermediate state after each step and test the invariant linking
  that state to the final output.

Simplification Boundary:
This is a local contract fixture demonstrating intermediate state tracking and invariant verification.
It does not implement full async networking or remote MCP transports.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Union
import json
import time


# ---------------------------------------------------------------------------
# State Stages and Models
# ---------------------------------------------------------------------------

class DispatchStage(str, Enum):
    INITIALIZED = "INITIALIZED"
    PARSED = "PARSED"
    ALLOWLIST_CHECKED = "ALLOWLIST_CHECKED"
    SCHEMA_VALIDATED = "SCHEMA_VALIDATED"
    DISPATCHING = "DISPATCHING"
    EXECUTED = "EXECUTED"
    FAILED = "FAILED"


@dataclass
class StepRecord:
    """Record of an intermediate state captured after a specific pipeline step."""
    step: int
    stage: str
    status: str  # "SUCCESS" | "FAILURE"
    details: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "step": self.step,
            "stage": self.stage,
            "status": self.status,
            "details": self.details
        }


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
    """Standardized response envelope including the full intermediate state trace."""
    success: bool
    tool: Optional[str]
    result: Optional[Union[int, float]] = None
    error: Optional[ToolError] = None
    state_trace: List[StepRecord] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "tool": self.tool,
            "result": self.result,
            "error": self.error.to_dict() if self.error else None,
            "state_trace": [s.to_dict() for s in self.state_trace]
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
# Invariant Verifier (Focus of Lab)
# ---------------------------------------------------------------------------

class InvariantVerifier:
    """
    Verifies formal invariants linking the sequence of recorded intermediate
    states to the final ToolResponse properties.
    """

    @staticmethod
    def verify(response: ToolResponse, expected_tool: Optional[str] = None) -> bool:
        stages = [s.stage for s in response.state_trace]
        statuses = [s.status for s in response.state_trace]

        # Invariant 1: Non-empty trace starting with INITIALIZED
        if not response.state_trace or response.state_trace[0].stage != DispatchStage.INITIALIZED.value:
            raise AssertionError("Invariant violation: state trace must begin with INITIALIZED")

        # Invariant 2: Success links directly to full pipeline completion
        if response.success:
            if response.error is not None:
                raise AssertionError("Invariant violation: successful response cannot contain an error")
            if response.result is None:
                raise AssertionError("Invariant violation: successful response must contain a numeric result")
            expected_stages = [
                DispatchStage.INITIALIZED.value,
                DispatchStage.PARSED.value,
                DispatchStage.ALLOWLIST_CHECKED.value,
                DispatchStage.SCHEMA_VALIDATED.value,
                DispatchStage.DISPATCHING.value,
                DispatchStage.EXECUTED.value,
            ]
            if stages != expected_stages:
                raise AssertionError(f"Invariant violation: successful stages {stages} != {expected_stages}")
            if any(status != "SUCCESS" for status in statuses):
                raise AssertionError("Invariant violation: all steps in successful execution must have SUCCESS status")
            return True

        # Invariant 3: Failure links to halting at the exact failure stage
        if response.error is None:
            raise AssertionError("Invariant violation: unsuccessful response must contain a structured error")
        if response.result is not None:
            raise AssertionError("Invariant violation: unsuccessful response cannot contain a result")

        # The last recorded step must be a FAILURE
        last_step = response.state_trace[-1]
        if last_step.status != "FAILURE":
            raise AssertionError("Invariant violation: terminal step in failed execution must be FAILURE")

        # Ensure no subsequent stages were executed
        if DispatchStage.EXECUTED.value in stages:
            raise AssertionError("Invariant violation: EXECUTED stage must never be reached in a failed call")

        # Specific Invariant for Unknown Tool: halts at ALLOWLIST_CHECKED
        if response.error.code == "UNKNOWN_TOOL":
            if last_step.stage != DispatchStage.ALLOWLIST_CHECKED.value:
                raise AssertionError(f"Invariant violation: UNKNOWN_TOOL must halt at ALLOWLIST_CHECKED, got {last_step.stage}")
            if DispatchStage.SCHEMA_VALIDATED.value in stages or DispatchStage.DISPATCHING.value in stages:
                raise AssertionError("Invariant violation: UNKNOWN_TOOL must never perform schema validation or dispatching")

        # Specific Invariant for Invalid Argument: halts at SCHEMA_VALIDATED
        if response.error.code == "INVALID_ARGUMENT":
            if last_step.stage != DispatchStage.SCHEMA_VALIDATED.value:
                raise AssertionError(f"Invariant violation: INVALID_ARGUMENT must halt at SCHEMA_VALIDATED, got {last_step.stage}")
            if DispatchStage.DISPATCHING.value in stages:
                raise AssertionError("Invariant violation: INVALID_ARGUMENT must never enter DISPATCHING stage")

        return True


# ---------------------------------------------------------------------------
# Tool Dispatcher with Step-by-Step State Recording
# ---------------------------------------------------------------------------

class LocalToolDispatcher:
    """
    Dispatches tool calls through an explicit allowlist and argument validation,
    recording intermediate state after each pipeline step.
    """

    ALLOWED_TOOLS: Set[str] = {"add", "multiply"}

    def __init__(self, tools: Optional[CalculatorTools] = None):
        self.tools = tools or CalculatorTools()

    def _validate_numeric(self, param_name: str, value: Any) -> Optional[ToolError]:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return ToolError(
                code="INVALID_ARGUMENT",
                message=f"Argument '{param_name}' must be a numeric value (int or float), got {type(value).__name__}.",
                details={"param": param_name, "value": value, "type": type(value).__name__}
            )
        return None

    def dispatch(self, raw_call: Union[str, Dict[str, Any]]) -> ToolResponse:
        trace: List[StepRecord] = []
        step_counter = 1

        # Step 1: Initialized
        trace.append(StepRecord(
            step=step_counter,
            stage=DispatchStage.INITIALIZED.value,
            status="SUCCESS",
            details={"raw_call_type": type(raw_call).__name__}
        ))
        step_counter += 1

        # Step 2: Parse Request
        if isinstance(raw_call, str):
            try:
                call_data = json.loads(raw_call)
            except json.JSONDecodeError as err:
                trace.append(StepRecord(
                    step=step_counter,
                    stage=DispatchStage.PARSED.value,
                    status="FAILURE",
                    details={"error": str(err)}
                ))
                return ToolResponse(
                    success=False,
                    tool=None,
                    error=ToolError(code="PARSE_ERROR", message=f"Malformed JSON: {err}"),
                    state_trace=trace
                )
        elif isinstance(raw_call, dict):
            call_data = raw_call
        else:
            trace.append(StepRecord(
                step=step_counter,
                stage=DispatchStage.PARSED.value,
                status="FAILURE",
                details={"error": "Invalid request type"}
            ))
            return ToolResponse(
                success=False,
                tool=None,
                error=ToolError(code="INVALID_REQUEST", message="Request must be a dictionary or JSON string."),
                state_trace=trace
            )

        trace.append(StepRecord(
            step=step_counter,
            stage=DispatchStage.PARSED.value,
            status="SUCCESS",
            details={"keys": list(call_data.keys())}
        ))
        step_counter += 1

        tool_name = call_data.get("tool")
        arguments = call_data.get("arguments")

        # Step 3: Check Allowlist
        if tool_name not in self.ALLOWED_TOOLS:
            trace.append(StepRecord(
                step=step_counter,
                stage=DispatchStage.ALLOWLIST_CHECKED.value,
                status="FAILURE",
                details={"requested_tool": tool_name, "allowed_tools": sorted(list(self.ALLOWED_TOOLS))}
            ))
            return ToolResponse(
                success=False,
                tool=tool_name,
                error=ToolError(
                    code="UNKNOWN_TOOL",
                    message=f"Tool '{tool_name}' is not in the allowlist. Allowed: {sorted(list(self.ALLOWED_TOOLS))}.",
                    details={"tool": tool_name, "allowed": sorted(list(self.ALLOWED_TOOLS))}
                ),
                state_trace=trace
            )

        trace.append(StepRecord(
            step=step_counter,
            stage=DispatchStage.ALLOWLIST_CHECKED.value,
            status="SUCCESS",
            details={"verified_tool": tool_name}
        ))
        step_counter += 1

        # Step 4: Validate Arguments Schema
        if not isinstance(arguments, dict):
            trace.append(StepRecord(
                step=step_counter,
                stage=DispatchStage.SCHEMA_VALIDATED.value,
                status="FAILURE",
                details={"error": "arguments not a dictionary"}
            ))
            return ToolResponse(
                success=False,
                tool=tool_name,
                error=ToolError(
                    code="INVALID_ARGUMENTS_STRUCTURE",
                    message="The 'arguments' payload must be a dictionary.",
                    details={"tool": tool_name}
                ),
                state_trace=trace
            )

        for param in ("a", "b"):
            if param not in arguments:
                trace.append(StepRecord(
                    step=step_counter,
                    stage=DispatchStage.SCHEMA_VALIDATED.value,
                    status="FAILURE",
                    details={"missing_param": param}
                ))
                return ToolResponse(
                    success=False,
                    tool=tool_name,
                    error=ToolError(
                        code="MISSING_ARGUMENT",
                        message=f"Missing required parameter '{param}'.",
                        details={"param": param}
                    ),
                    state_trace=trace
                )

        err_a = self._validate_numeric("a", arguments["a"])
        if err_a:
            trace.append(StepRecord(
                step=step_counter,
                stage=DispatchStage.SCHEMA_VALIDATED.value,
                status="FAILURE",
                details={"param": "a", "error": err_a.message}
            ))
            return ToolResponse(success=False, tool=tool_name, error=err_a, state_trace=trace)

        err_b = self._validate_numeric("b", arguments["b"])
        if err_b:
            trace.append(StepRecord(
                step=step_counter,
                stage=DispatchStage.SCHEMA_VALIDATED.value,
                status="FAILURE",
                details={"param": "b", "error": err_b.message}
            ))
            return ToolResponse(success=False, tool=tool_name, error=err_b, state_trace=trace)

        trace.append(StepRecord(
            step=step_counter,
            stage=DispatchStage.SCHEMA_VALIDATED.value,
            status="SUCCESS",
            details={"a": arguments["a"], "b": arguments["b"]}
        ))
        step_counter += 1

        # Step 5: Dispatching
        trace.append(StepRecord(
            step=step_counter,
            stage=DispatchStage.DISPATCHING.value,
            status="SUCCESS",
            details={"target_handler": tool_name}
        ))
        step_counter += 1

        # Step 6: Executed
        if tool_name == "add":
            res = self.tools.add(arguments["a"], arguments["b"])
        elif tool_name == "multiply":
            res = self.tools.multiply(arguments["a"], arguments["b"])
        else:
            trace.append(StepRecord(
                step=step_counter,
                stage=DispatchStage.EXECUTED.value,
                status="FAILURE",
                details={"error": f"Unmapped tool: {tool_name}"}
            ))
            return ToolResponse(
                success=False,
                tool=tool_name,
                error=ToolError(code="UNKNOWN_TOOL", message=f"Unmapped tool '{tool_name}'."),
                state_trace=trace
            )

        trace.append(StepRecord(
            step=step_counter,
            stage=DispatchStage.EXECUTED.value,
            status="SUCCESS",
            details={"computed_result": res}
        ))

        return ToolResponse(
            success=True,
            tool=tool_name,
            result=res,
            state_trace=trace
        )

    def dispatch_batch(self, calls: List[Dict[str, Any]], stop_on_failure: bool = True) -> List[ToolResponse]:
        results: List[ToolResponse] = []
        for call in calls:
            res = self.dispatch(call)
            results.append(res)
            if not res.success and stop_on_failure:
                break
        return results


# ---------------------------------------------------------------------------
# CLI / Demonstration
# ---------------------------------------------------------------------------

def run_demo() -> None:
    dispatcher = LocalToolDispatcher()
    fixtures = [
        ("Valid add(2, 3)", {"tool": "add", "arguments": {"a": 2, "b": 3}}),
        ("Valid multiply(2, 3)", {"tool": "multiply", "arguments": {"a": 2, "b": 3}}),
        ("Invalid Unknown Tool", {"tool": "divide", "arguments": {"a": 10, "b": 2}}),
        ("Invalid String 'a'", {"tool": "add", "arguments": {"a": "2", "b": 3}}),
    ]

    print("=" * 80)
    print("Applied Lab R49-T024: Intermediate State Trace & Invariant Verification")
    print("=" * 80)
    for label, payload in fixtures:
        resp = dispatcher.dispatch(payload)
        is_valid = InvariantVerifier.verify(resp)
        print(f"\n[{label}] (Invariant Holds: {is_valid})")
        print(f"  Result: {resp.result if resp.success else resp.error.message}")
        print("  State Trace Sequence:")
        for step in resp.state_trace:
            print(f"    Step {step.step}: [{step.stage}] -> {step.status} | Details: {step.details}")


if __name__ == "__main__":
    run_demo()
