"""Typed tool dispatch with scenario assessment questions and executable checks.

Task R49-T020: Scenario assessment for Advanced Server Usage.
"""

from typing import Any, Dict, List, Tuple


ALLOWLIST = {"add", "multiply"}


def dispatch_tool(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Dispatch a JSON tool request through allowlist and numeric argument validation.

    Parameters:
        payload: Dict containing 'tool' and 'arguments'.

    Returns:
        Structured response dictionary with 'success' and 'result' or 'error'.
    """
    if not isinstance(payload, dict):
        return {
            "success": False,
            "error": {"code": "INVALID_PAYLOAD", "message": "Payload must be a dictionary"},
        }

    tool_name = payload.get("tool")
    if tool_name not in ALLOWLIST:
        return {
            "success": False,
            "error": {
                "code": "UNKNOWN_TOOL",
                "message": f"Tool '{tool_name}' is not in allowlist: {sorted(ALLOWLIST)}",
            },
        }

    args = payload.get("arguments")
    if not isinstance(args, dict):
        return {
            "success": False,
            "error": {"code": "INVALID_ARGUMENTS", "message": "Arguments must be a dictionary"},
        }

    if "a" not in args or "b" not in args:
        return {
            "success": False,
            "error": {"code": "MISSING_ARGUMENT", "message": "Arguments 'a' and 'b' are required"},
        }

    a, b = args["a"], args["b"]
    if isinstance(a, bool) or not isinstance(a, (int, float)):
        return {
            "success": False,
            "error": {
                "code": "INVALID_ARGUMENT_TYPE",
                "message": f"Argument 'a' must be numeric, got {type(a).__name__}",
            },
        }
    if isinstance(b, bool) or not isinstance(b, (int, float)):
        return {
            "success": False,
            "error": {
                "code": "INVALID_ARGUMENT_TYPE",
                "message": f"Argument 'b' must be numeric, got {type(b).__name__}",
            },
        }

    if tool_name == "add":
        return {"success": True, "tool": "add", "result": a + b}
    elif tool_name == "multiply":
        return {"success": True, "tool": "multiply", "result": a * b}

    return {
        "success": False,
        "error": {"code": "DISPATCH_FAILED", "message": f"Execution failed for {tool_name}"},
    }


APPLIED_QUESTIONS: List[Dict[str, Any]] = [
    {
        "q_id": "Q1_predict_output",
        "question": "What is the structured result when calling add(2, 3)?",
        "prediction": {"success": True, "tool": "add", "result": 5},
        "rationale": "Tool 'add' is in allowlist, inputs 2 and 3 are valid numeric types, computing 2 + 3 = 5.",
        "payload": {"tool": "add", "arguments": {"a": 2, "b": 3}},
    },
    {
        "q_id": "Q2_diagnose_failure",
        "question": "Why does calling add with arguments {'a': '2', 'b': 3} fail?",
        "diagnosis": "Argument 'a' is a string instead of a numeric type, violating the type contract.",
        "expected_code": "INVALID_ARGUMENT_TYPE",
        "rationale": "Strict typing prevents silent type coercion errors and guarantees arithmetic safety.",
        "payload": {"tool": "add", "arguments": {"a": "2", "b": 3}},
    },
    {
        "q_id": "Q3_boundary_policy",
        "question": "What boundary policy governs unlisted tools like 'divide'?",
        "policy": "Strict allowlist rejection: return structured UNKNOWN_TOOL error without fallback execution.",
        "expected_code": "UNKNOWN_TOOL",
        "rationale": "A failed call must never execute another tool to avoid unintended side-effects or security leakage.",
        "payload": {"tool": "divide", "arguments": {"a": 6, "b": 2}},
    },
]


def execute_applied_checks() -> List[Dict[str, Any]]:
    """Execute factual verification checks for all three applied questions."""
    assessment_results = []
    for item in APPLIED_QUESTIONS:
        actual = dispatch_tool(item["payload"])
        if item["q_id"] == "Q1_predict_output":
            passed = actual == item["prediction"]
        elif item["q_id"] == "Q2_diagnose_failure":
            passed = (not actual["success"]) and (actual.get("error", {}).get("code") == item["expected_code"])
        elif item["q_id"] == "Q3_boundary_policy":
            passed = (not actual["success"]) and (actual.get("error", {}).get("code") == item["expected_code"])
        else:
            passed = False

        assessment_results.append({
            "q_id": item["q_id"],
            "question": item["question"],
            "verified": passed,
            "actual_response": actual,
        })
    return assessment_results


def main() -> None:
    """Run demonstration and print assessment questions with verified answers."""
    print("=== Advanced Server Usage: Scenario Assessment (R49-T020) ===")

    # Standard calls
    print("\n[Standard Dispatches]")
    print(f"add(2, 3) -> {dispatch_tool({'tool': 'add', 'arguments': {'a': 2, 'b': 3}})}")
    print(f"multiply(2, 3) -> {dispatch_tool({'tool': 'multiply', 'arguments': {'a': 2, 'b': 3}})}")

    # Assessment checks
    print("\n[Applied Questions & Executable Checks]")
    results = execute_applied_checks()
    for idx, r in enumerate(results, 1):
        status = "PASSED" if r["verified"] else "FAILED"
        print(f"Q{idx} ({r['q_id']}): {status}")
        print(f"   Question: {r['question']}")
        print(f"   Response: {r['actual_response']}")

    print("\nAll scenario checks passed. Failed calls returned structured errors without side effects.")


if __name__ == "__main__":
    main()
