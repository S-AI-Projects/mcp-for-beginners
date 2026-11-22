"""
Applied Lab R49-T029: Tool Dispatch Benchmarking across Controlled Deployment Configurations.

Lesson Context (03-GettingStarted/09-deployment/README.md):
When deploying MCP servers across different environments (local CLI, lightweight serverless
functions, or enterprise container apps), deployment configurations must balance memory footprint,
diagnostic telemetry, and dispatch throughput while strictly maintaining contract correctness.

Contract Requirements:
- Explicit allowlist: only 'add' and 'multiply' can execute.
- Strict numeric validation: 'a' and 'b' must be numbers (int or float; strictly reject bool and str).
- Expected operations: add(2, 3) -> 5; multiply(2, 3) -> 6.
- Structured errors: unknown tool and string 'a' are structured errors.
- Failure isolation: a failed call cannot execute another tool.
- Focus: Compare three small controlled configurations or input sizes using a metric
  appropriate to this contract. Report correctness and the observed trade-off without
  claiming real-world model accuracy.

Simplification Boundary:
This is a local contract fixture demonstrating controlled configuration trade-offs.
It does not claim real-world cloud service performance, network latency, or model accuracy.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple, Union
import json
import time


# ---------------------------------------------------------------------------
# Data Models and Error Envelopes
# ---------------------------------------------------------------------------

@dataclass
class ToolError:
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
    success: bool
    tool: Optional[str]
    result: Optional[Union[int, float]] = None
    error: Optional[ToolError] = None
    execution_time_us: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "tool": self.tool,
            "result": self.result,
            "error": self.error.to_dict() if self.error else None,
            "execution_time_us": self.execution_time_us
        }


# ---------------------------------------------------------------------------
# Tool Handlers
# ---------------------------------------------------------------------------

class CalculatorTools:
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
# Deployment Configurations
# ---------------------------------------------------------------------------

@dataclass
class DeploymentProfile:
    name: str
    record_telemetry: bool
    max_history_buffer: int
    deep_payload_copy: bool
    description: str


PROFILES: Dict[str, DeploymentProfile] = {
    "minimal": DeploymentProfile(
        name="minimal_embedded",
        record_telemetry=False,
        max_history_buffer=0,
        deep_payload_copy=False,
        description="Zero telemetry buffer for ultra-low memory footprints (e.g. CLI sidecars)."
    ),
    "standard": DeploymentProfile(
        name="standard_container",
        record_telemetry=True,
        max_history_buffer=50,
        deep_payload_copy=False,
        description="Bounded telemetry buffer for standard container deployments (e.g. Azure Container Apps)."
    ),
    "diagnostic": DeploymentProfile(
        name="enterprise_diagnostic",
        record_telemetry=True,
        max_history_buffer=500,
        deep_payload_copy=True,
        description="Deep auditing with full payload cloning for enterprise diagnostic tracing."
    ),
}


# ---------------------------------------------------------------------------
# Configurable Tool Dispatcher
# ---------------------------------------------------------------------------

class ConfigurableToolDispatcher:
    """
    Dispatches tool calls with configurable deployment telemetry and memory settings.
    """

    ALLOWED_TOOLS: Set[str] = {"add", "multiply"}

    def __init__(
        self,
        profile: Optional[DeploymentProfile] = None,
        tools: Optional[CalculatorTools] = None
    ):
        self.profile = profile or PROFILES["standard"]
        self.tools = tools or CalculatorTools()
        self.history: List[Dict[str, Any]] = []

    def _validate_numeric(self, param: str, val: Any) -> Optional[ToolError]:
        if isinstance(val, bool) or not isinstance(val, (int, float)):
            return ToolError(
                code="INVALID_ARGUMENT",
                message=f"Argument '{param}' must be a numeric value (int or float), got {type(val).__name__}.",
                details={"param": param, "value": val, "type": type(val).__name__}
            )
        return None

    def dispatch(self, raw_call: Union[str, Dict[str, Any]]) -> ToolResponse:
        start_t = time.perf_counter_ns()

        if isinstance(raw_call, str):
            try:
                call_data = json.loads(raw_call)
            except json.JSONDecodeError as err:
                resp = ToolResponse(
                    success=False,
                    tool=None,
                    error=ToolError(code="PARSE_ERROR", message=f"Malformed JSON: {err}")
                )
                self._record_telemetry(raw_call, resp)
                return resp
        elif isinstance(raw_call, dict):
            call_data = raw_call
        else:
            resp = ToolResponse(
                success=False,
                tool=None,
                error=ToolError(code="INVALID_REQUEST", message="Request must be a dictionary or JSON string.")
            )
            self._record_telemetry(raw_call, resp)
            return resp

        tool_name = call_data.get("tool")
        arguments = call_data.get("arguments")

        # 1. Allowlist Check
        if tool_name not in self.ALLOWED_TOOLS:
            resp = ToolResponse(
                success=False,
                tool=tool_name,
                error=ToolError(
                    code="UNKNOWN_TOOL",
                    message=f"Tool '{tool_name}' is not in the allowlist. Allowed: {sorted(list(self.ALLOWED_TOOLS))}.",
                    details={"tool": tool_name}
                )
            )
            self._record_telemetry(call_data, resp)
            return resp

        # 2. Argument Dictionary Check
        if not isinstance(arguments, dict):
            resp = ToolResponse(
                success=False,
                tool=tool_name,
                error=ToolError(code="INVALID_ARGUMENTS_STRUCTURE", message="Arguments must be a dictionary.")
            )
            self._record_telemetry(call_data, resp)
            return resp

        # 3. Missing Argument Check
        for param in ("a", "b"):
            if param not in arguments:
                resp = ToolResponse(
                    success=False,
                    tool=tool_name,
                    error=ToolError(code="MISSING_ARGUMENT", message=f"Missing parameter '{param}'.")
                )
                self._record_telemetry(call_data, resp)
                return resp

        # 4. Strict Numeric Type Validation
        err_a = self._validate_numeric("a", arguments["a"])
        if err_a:
            resp = ToolResponse(success=False, tool=tool_name, error=err_a)
            self._record_telemetry(call_data, resp)
            return resp

        err_b = self._validate_numeric("b", arguments["b"])
        if err_b:
            resp = ToolResponse(success=False, tool=tool_name, error=err_b)
            self._record_telemetry(call_data, resp)
            return resp

        # 5. Execute Handler
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
            self._record_telemetry(call_data, resp)
            return resp

        elapsed_us = (time.perf_counter_ns() - start_t) / 1000.0
        resp = ToolResponse(success=True, tool=tool_name, result=res, execution_time_us=elapsed_us)
        self._record_telemetry(call_data, resp)
        return resp

    def _record_telemetry(self, request_payload: Any, response: ToolResponse) -> None:
        if not self.profile.record_telemetry or self.profile.max_history_buffer <= 0:
            return

        if len(self.history) >= self.profile.max_history_buffer:
            self.history.pop(0)  # Evict oldest entry (FIFO)

        if self.profile.deep_payload_copy:
            cloned_req = json.loads(json.dumps(request_payload)) if isinstance(request_payload, (dict, list)) else request_payload
            cloned_resp = response.to_dict()
            self.history.append({"request": cloned_req, "response": cloned_resp})
        else:
            self.history.append({"tool": response.tool, "success": response.success})

    def dispatch_batch(self, calls: List[Dict[str, Any]], stop_on_failure: bool = True) -> List[ToolResponse]:
        results: List[ToolResponse] = []
        for call in calls:
            res = self.dispatch(call)
            results.append(res)
            if not res.success and stop_on_failure:
                break
        return results


# ---------------------------------------------------------------------------
# Controlled Configuration Benchmark & Trade-off Comparison
# ---------------------------------------------------------------------------

def benchmark_configurations(call_count: int = 50) -> List[Dict[str, Any]]:
    """
    Compares the 3 controlled deployment profiles on identical input batches.
    Reports:
    - Correctness rate (100% expected)
    - Memory footprint (retained history records)
    - Total execution time (microseconds)
    - Trade-off description
    """
    # Deterministic test batch with valid calls and errors
    batch: List[Dict[str, Any]] = []
    for i in range(call_count):
        if i % 5 == 0:
            # Scheduled error case to verify error handling across configs
            batch.append({"tool": "divide", "arguments": {"a": i, "b": 2}})
        elif i % 2 == 0:
            batch.append({"tool": "add", "arguments": {"a": i, "b": 2}})
        else:
            batch.append({"tool": "multiply", "arguments": {"a": i, "b": 3}})

    metrics = []
    for key in ["minimal", "standard", "diagnostic"]:
        profile = PROFILES[key]
        dispatcher = ConfigurableToolDispatcher(profile=profile)

        start_ns = time.perf_counter_ns()
        # Batch with stop_on_failure=False to evaluate throughput over full batch
        results = [dispatcher.dispatch(c) for c in batch]
        total_time_us = (time.perf_counter_ns() - start_ns) / 1000.0

        # Evaluate correctness
        correct_count = 0
        for idx, (call, res) in enumerate(zip(batch, results)):
            if call["tool"] == "divide":
                if not res.success and res.error and res.error.code == "UNKNOWN_TOOL":
                    correct_count += 1
            elif call["tool"] == "add":
                if res.success and res.result == call["arguments"]["a"] + 2:
                    correct_count += 1
            elif call["tool"] == "multiply":
                if res.success and res.result == call["arguments"]["a"] * 3:
                    correct_count += 1

        correctness_pct = (correct_count / len(batch)) * 100.0

        metrics.append({
            "profile_key": key,
            "profile_name": profile.name,
            "total_calls": len(batch),
            "correct_calls": correct_count,
            "correctness_percentage": correctness_pct,
            "retained_memory_records": len(dispatcher.history),
            "total_time_us": round(total_time_us, 2),
            "avg_time_per_call_us": round(total_time_us / len(batch), 2),
            "trade_off_analysis": (
                f"{profile.name}: {len(dispatcher.history)} telemetry records retained. "
                f"Trade-off: {'Zero memory overhead with no audit trail' if key == 'minimal' else 'Bounded buffer with operational metrics' if key == 'standard' else 'Maximum diagnostic fidelity with full payload memory cost'}."
            )
        })

    return metrics


def run_demo() -> None:
    print("=" * 80)
    print("Applied Lab R49-T029: Controlled Deployment Configuration Benchmarking")
    print("=" * 80)
    metrics = benchmark_configurations(call_count=30)
    for m in metrics:
        print(f"\n[Configuration: {m['profile_name']}]")
        print(f"  Total Calls:      {m['total_calls']}")
        print(f"  Correctness:      {m['correctness_percentage']}% ({m['correct_calls']}/{m['total_calls']})")
        print(f"  Retained Memory:  {m['retained_memory_records']} audit records")
        print(f"  Avg Latency/Call: {m['avg_time_per_call_us']} µs")
        print(f"  Trade-off:        {m['trade_off_analysis']}")


if __name__ == "__main__":
    run_demo()
