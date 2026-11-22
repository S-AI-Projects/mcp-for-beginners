"""
MCP Server Implementation - Typed Tool Dispatch, Explicit Allowlist & Numeric Validation.

Lesson Extension: 11-MCPServerHandsOnLabs/05-MCP-Server
Task ID: R49-T035

Key Contract:
- Explicit allowlist strictly containing {"add", "multiply"}.
- Numeric validation on arguments (a, b) requiring int or float.
- add(2, 3) -> 5
- multiply(2, 3) -> 6
- Unknown tool yields structured JSON-RPC error (-32601).
- Non-numeric argument (e.g. string 'a') yields structured JSON-RPC error (-32602).
- Execution Isolation: A failed call cannot execute another tool.
- Worked explanation and regression test execution.
"""

from dataclasses import dataclass
import json
from typing import Any, Callable, Dict, List, Optional, Set, Tuple


# JSON-RPC Standard Error Codes
METHOD_NOT_FOUND = -32601
INVALID_PARAMS = -32602

# Explicit Tool Allowlist
TOOL_ALLOWLIST: Set[str] = {"add", "multiply"}


# Worked Input-to-Output Reference Table for Regression Testing
WORKED_EXAMPLES: List[Dict[str, Any]] = [
    {
        "description": "Valid add operation with integers 2 and 3",
        "input": {"jsonrpc": "2.0", "id": 1, "tool": "add", "params": {"a": 2, "b": 3}},
        "expected_status": "SUCCESS",
        "expected_value": 5,
        "expected_error_code": None,
        "phase_breakdown": [
            "1. Allowlist check: 'add' is in {'add', 'multiply'} -> ALLOWED",
            "2. Type validation: a=2 (int), b=3 (int) -> VALID",
            "3. Execution: add(2, 3) -> 5",
            "4. Envelope: {'jsonrpc': '2.0', 'id': 1, 'result': {'value': 5, 'tool': 'add'}}"
        ]
    },
    {
        "description": "Valid multiply operation with integers 2 and 3",
        "input": {"jsonrpc": "2.0", "id": 2, "tool": "multiply", "params": {"a": 2, "b": 3}},
        "expected_status": "SUCCESS",
        "expected_value": 6,
        "expected_error_code": None,
        "phase_breakdown": [
            "1. Allowlist check: 'multiply' is in {'add', 'multiply'} -> ALLOWED",
            "2. Type validation: a=2 (int), b=3 (int) -> VALID",
            "3. Execution: multiply(2, 3) -> 6",
            "4. Envelope: {'jsonrpc': '2.0', 'id': 2, 'result': {'value': 6, 'tool': 'multiply'}}"
        ]
    },
    {
        "description": "Unknown tool invocation ('power')",
        "input": {"jsonrpc": "2.0", "id": 3, "tool": "power", "params": {"a": 2, "b": 3}},
        "expected_status": "ERROR",
        "expected_value": None,
        "expected_error_code": METHOD_NOT_FOUND,
        "phase_breakdown": [
            "1. Allowlist check: 'power' not in {'add', 'multiply'} -> REJECTED",
            "2. Type validation: SKIPPED (fails fast)",
            "3. Execution: ABORTED (zero tools executed)",
            "4. Envelope: Structured error code -32601"
        ]
    },
    {
        "description": "Invalid parameter: string 'a' passed to add()",
        "input": {"jsonrpc": "2.0", "id": 4, "tool": "add", "params": {"a": "2", "b": 3}},
        "expected_status": "ERROR",
        "expected_value": None,
        "expected_error_code": INVALID_PARAMS,
        "phase_breakdown": [
            "1. Allowlist check: 'add' is in allowlist -> ALLOWED",
            "2. Type validation: a='2' (str, expected int/float) -> REJECTED",
            "3. Execution: ABORTED (zero tools executed)",
            "4. Envelope: Structured error code -32602"
        ]
    }
]


class TypedToolDispatcher:
    """
    Enforces allowlist authorization, strict numeric argument validation,
    and safe isolated execution.
    """

    def __init__(self):
        self.allowlist: Set[str] = set(TOOL_ALLOWLIST)
        self.handlers: Dict[str, Callable[[float, float], float]] = {
            "add": lambda a, b: a + b,
            "multiply": lambda a, b: a * b
        }
        self.execution_counts: Dict[str, int] = {
            "add": 0,
            "multiply": 0
        }

    def dispatch(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Dispatch a tool call.
        Enforces:
        - Tool allowlist verification before inspection.
        - Numeric validation on 'a' and 'b'.
        - On validation failure, execution halts immediately with zero side-effects.
        """
        req_id = request.get("id")
        tool = request.get("tool") or request.get("method")

        # 1. Allowlist Check
        if not tool or tool not in self.allowlist:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {
                    "code": METHOD_NOT_FOUND,
                    "message": f"Method not found: Tool '{tool}' is not allowlisted."
                }
            }

        # 2. Extract & Validate Parameters
        params = request.get("params") or request.get("arguments") or {}
        if not isinstance(params, dict):
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {
                    "code": INVALID_PARAMS,
                    "message": "Invalid params: Parameters must be supplied as a dictionary."
                }
            }

        if "a" not in params or "b" not in params:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {
                    "code": INVALID_PARAMS,
                    "message": "Invalid params: Missing required parameters 'a' and 'b'."
                }
            }

        a = params["a"]
        b = params["b"]

        # Disallow boolean as numeric (bool is subclass of int in Python)
        if isinstance(a, bool) or not isinstance(a, (int, float)):
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {
                    "code": INVALID_PARAMS,
                    "message": f"Invalid params: Parameter 'a' must be numeric (int or float), got {type(a).__name__}."
                }
            }

        if isinstance(b, bool) or not isinstance(b, (int, float)):
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {
                    "code": INVALID_PARAMS,
                    "message": f"Invalid params: Parameter 'b' must be numeric (int or float), got {type(b).__name__}."
                }
            }

        # 3. Safe Execution (Only reaches here if all checks pass)
        self.execution_counts[tool] += 1
        res_value = self.handlers[tool](a, b)

        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "value": res_value,
                "tool": tool
            }
        }

    def get_tool_call_count(self, tool: str) -> int:
        return self.execution_counts.get(tool, 0)


def run_demonstration() -> Dict[str, Any]:
    """Execute worked input-to-output examples and print step-by-step breakdown."""
    print("=" * 75)
    print("MCP Typed Tool Dispatch: Worked Example & Allowlist Validation (R49-T035)")
    print("=" * 75)

    dispatcher = TypedToolDispatcher()
    demo_records = []

    for item in WORKED_EXAMPLES:
        print(f"\n[Case: {item['description']}]")
        print(f"  Input: {json.dumps(item['input'])}")
        print("  Worked Steps:")
        for step in item["phase_breakdown"]:
            print(f"    {step}")

        response = dispatcher.dispatch(item["input"])
        print(f"  Actual Response: {json.dumps(response)}")

        if item["expected_status"] == "SUCCESS":
            assert "result" in response
            assert response["result"]["value"] == item["expected_value"]
            print(f"  -> Verified: value={response['result']['value']} matches expected {item['expected_value']}")
        else:
            assert "error" in response
            assert response["error"]["code"] == item["expected_error_code"]
            print(f"  -> Verified: error code={response['error']['code']} matches expected {item['expected_error_code']}")

        demo_records.append({
            "description": item["description"],
            "input": item["input"],
            "response": response
        })

    print("\n" + "-" * 75)
    print(f"Tool Execution Counter: {dispatcher.execution_counts}")
    print("Failed calls strictly executed 0 tools. Circuit isolation confirmed.")
    print("=" * 75)

    return {
        "cases_verified": len(demo_records),
        "execution_counts": dispatcher.execution_counts
    }


if __name__ == "__main__":
    run_demonstration()
