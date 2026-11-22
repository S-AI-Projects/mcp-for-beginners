"""
MCP Monitoring & Observability - Trace Aggregation & Refactored Architecture.

Lesson Extension: 11-MCPServerHandsOnLabs/11-Monitoring
Task ID: R49-T036

Contract:
- Aggregate local trace records by request ID.
- Report duration, tool-call count, and success/failure status.
- Strict privacy: Prompts and user input strings are NEVER included in aggregated output.
- Request A: Two tool calls, duration exactly 12ms, status SUCCESS.
- Request B: Status FAILURE with error message.
- Missing end events: Marked status INCOMPLETE with duration None (never assigned 0).
- Focus: Implement a correct baseline (BaselineTraceAggregator), extract one named
  responsibility (TraceLifecycleClassifier), and prove before/after equivalence.
"""

from dataclasses import dataclass, field
import json
from typing import Any, Dict, List, Optional, Tuple


# Deterministic Local Trace Fixture
LOCAL_TRACE_FIXTURE: List[Dict[str, Any]] = [
    # Request A: Two tool calls, duration = 112 - 100 = 12ms, SUCCESS
    {"request_id": "req-A", "event": "start", "timestamp_ms": 100, "prompt": "SELECT sales FROM store_101"},
    {"request_id": "req-A", "event": "tool_call", "timestamp_ms": 104, "tool": "query_db"},
    {"request_id": "req-A", "event": "tool_call", "timestamp_ms": 108, "tool": "format_currency"},
    {"request_id": "req-A", "event": "end", "timestamp_ms": 112, "status": "ok"},

    # Request B: Fails with database error
    {"request_id": "req-B", "event": "start", "timestamp_ms": 200, "prompt": "UPDATE store_catalog SET price=10"},
    {"request_id": "req-B", "event": "error", "timestamp_ms": 205, "error": "Database connection timeout"},
    {"request_id": "req-B", "event": "end", "timestamp_ms": 205, "status": "error"},

    # Request C: Missing end event (crashed/interrupted) -> Must be INCOMPLETE, duration None
    {"request_id": "req-C", "event": "start", "timestamp_ms": 300, "prompt": "ANALYZE sales_forecast"},
    {"request_id": "req-C", "event": "tool_call", "timestamp_ms": 305, "tool": "compute_trends"},
]


# ==============================================================================
# Approach 1: Baseline Monolithic Implementation
# ==============================================================================

class BaselineTraceAggregator:
    """
    Monolithic baseline aggregator that performs grouping, lifecycle tracking,
    duration calculation, tool counting, and prompt redaction in a single unit.
    """

    def aggregate(self, trace_events: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        # Group events by request_id
        grouped: Dict[str, List[Dict[str, Any]]] = {}
        for ev in trace_events:
            rid = ev.get("request_id")
            if not rid:
                continue
            if rid not in grouped:
                grouped[rid] = []
            grouped[rid].append(ev)

        summary: Dict[str, Dict[str, Any]] = {}

        for rid, events in grouped.items():
            start_time = None
            end_time = None
            tool_calls = 0
            has_error = False
            error_msg = None
            has_end_event = False

            for ev in events:
                etype = ev.get("event")
                ts = ev.get("timestamp_ms")

                if etype == "start":
                    start_time = ts
                elif etype == "tool_call":
                    tool_calls += 1
                elif etype == "error":
                    has_error = True
                    error_msg = ev.get("error", "Unknown error")
                elif etype == "end":
                    end_time = ts
                    has_end_event = True
                    if ev.get("status") == "error":
                        has_error = True

            # Determine lifecycle status and duration
            if not has_end_event:
                status = "INCOMPLETE"
                duration_ms = None  # Crucial: Not 0!
            elif has_error:
                status = "FAILURE"
                duration_ms = (end_time - start_time) if (start_time is not None and end_time is not None) else None
            else:
                status = "SUCCESS"
                duration_ms = (end_time - start_time) if (start_time is not None and end_time is not None) else None

            # Prompt content is intentionally EXCLUDED
            summary[rid] = {
                "request_id": rid,
                "status": status,
                "duration_ms": duration_ms,
                "tool_call_count": tool_calls,
                "error": error_msg,
            }

        return summary


# ==============================================================================
# Approach 2: Refactored with Extracted Responsibility (TraceLifecycleClassifier)
# ==============================================================================

@dataclass
class LifecycleEvaluation:
    """Evaluated lifecycle status and duration for a single request."""
    status: str
    duration_ms: Optional[int]
    has_end_event: bool
    has_error: bool
    error_message: Optional[str]


class TraceLifecycleClassifier:
    """
    Extracted named responsibility:
    Specializes exclusively in evaluating event sequences, correlating start/end timestamps,
    detecting incomplete traces, and classifying lifecycle status.
    """

    def evaluate_lifecycle(self, events: List[Dict[str, Any]]) -> LifecycleEvaluation:
        start_time: Optional[int] = None
        end_time: Optional[int] = None
        has_end_event = False
        has_error = False
        error_msg: Optional[str] = None

        for ev in events:
            etype = ev.get("event")
            ts = ev.get("timestamp_ms")

            if etype == "start" and ts is not None:
                start_time = ts
            elif etype == "error":
                has_error = True
                error_msg = ev.get("error", "Unknown error")
            elif etype == "end":
                has_end_event = True
                if ts is not None:
                    end_time = ts
                if ev.get("status") == "error":
                    has_error = True

        # Lifecycle Decision Rule
        if not has_end_event:
            # Missing end event marked incomplete rather than assigned duration zero
            status = "INCOMPLETE"
            duration = None
        elif has_error:
            status = "FAILURE"
            duration = (end_time - start_time) if (start_time is not None and end_time is not None) else None
        else:
            status = "SUCCESS"
            duration = (end_time - start_time) if (start_time is not None and end_time is not None) else None

        return LifecycleEvaluation(
            status=status,
            duration_ms=duration,
            has_end_event=has_end_event,
            has_error=has_error,
            error_message=error_msg
        )


class RefactoredTraceAggregator:
    """
    Refactored aggregator coordinating grouping, prompt-stripping, and tool counting,
    delegating lifecycle evaluation to the extracted TraceLifecycleClassifier.
    """

    def __init__(self, lifecycle_classifier: Optional[TraceLifecycleClassifier] = None):
        self.classifier = lifecycle_classifier or TraceLifecycleClassifier()

    def aggregate(self, trace_events: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        # 1. Group events by request_id
        grouped: Dict[str, List[Dict[str, Any]]] = {}
        for ev in trace_events:
            rid = ev.get("request_id")
            if not rid:
                continue
            if rid not in grouped:
                grouped[rid] = []
            grouped[rid].append(ev)

        summary: Dict[str, Dict[str, Any]] = {}

        for rid, events in grouped.items():
            # 2. Count tools
            tool_calls = sum(1 for ev in events if ev.get("event") == "tool_call")

            # 3. Delegate lifecycle & duration to extracted classifier
            lifecycle = self.classifier.evaluate_lifecycle(events)

            # 4. Construct aggregated record (Strictly prompt-free)
            summary[rid] = {
                "request_id": rid,
                "status": lifecycle.status,
                "duration_ms": lifecycle.duration_ms,
                "tool_call_count": tool_calls,
                "error": lifecycle.error_message,
            }

        return summary


def verify_before_after_equivalence(
    trace_events: Optional[List[Dict[str, Any]]] = None
) -> Tuple[bool, Dict[str, Any], Dict[str, Any]]:
    """
    Prove that BaselineTraceAggregator and RefactoredTraceAggregator yield
    100% identical outputs for identical inputs.
    """
    events = trace_events if trace_events is not None else list(LOCAL_TRACE_FIXTURE)

    baseline = BaselineTraceAggregator()
    refactored = RefactoredTraceAggregator()

    baseline_res = baseline.aggregate(events)
    refactored_res = refactored.aggregate(events)

    is_equivalent = (baseline_res == refactored_res)
    return is_equivalent, baseline_res, refactored_res


def run_demonstration() -> Dict[str, Any]:
    """Execute aggregation, display report, and prove before/after equivalence."""
    print("=" * 75)
    print("MCP Monitoring: Trace Aggregation & Refactoring Equivalence (R49-T036)")
    print("=" * 75)

    is_equiv, baseline_output, refactored_output = verify_before_after_equivalence()

    print("\n[Aggregated Trace Summary]")
    for rid, record in refactored_output.items():
        print(f"  Request ID       : {record['request_id']}")
        print(f"    Status         : {record['status']}")
        print(f"    Duration       : {record['duration_ms']} ms" if record['duration_ms'] is not None else "    Duration       : None (Incomplete)")
        print(f"    Tool Calls     : {record['tool_call_count']}")
        print(f"    Error          : {record['error']}")
        print()

    # Privacy verification
    dumped_str = json.dumps(refactored_output)
    prompts_leaked = any(ev.get("prompt") in dumped_str for ev in LOCAL_TRACE_FIXTURE if "prompt" in ev)
    has_prompt_key = "prompt" in dumped_str

    print("-" * 75)
    print(f"Before/After Equivalence Proof : {'PASSED (Identical)' if is_equiv else 'FAILED'}")
    print(f"Prompt Redaction Verification  : {'PASSED (Zero Leaks)' if not (prompts_leaked or has_prompt_key) else 'FAILED'}")
    print(f"Missing End Handling Check     : Request C duration is None: {refactored_output['req-C']['duration_ms'] is None}")
    print("=" * 75)

    return {
        "equivalence": is_equiv,
        "prompts_leaked": prompts_leaked,
        "req_a": refactored_output.get("req-A"),
        "req_b": refactored_output.get("req-B"),
        "req_c": refactored_output.get("req-C"),
    }


if __name__ == "__main__":
    run_demonstration()
