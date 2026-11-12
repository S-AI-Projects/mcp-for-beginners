"""Local mock for validating and dispatching typed tool calls."""

import json
import math


def add(a, b):
    return a + b


def multiply(a, b):
    return a * b


TOOLS = {
    "add": add,
    "multiply": multiply,
}


def dispatch(name, arguments):
    """Dispatch an allowed tool after validating numeric arguments."""

    if name not in TOOLS:
        return {
            "ok": False,
            "error": {
                "code": "UNKNOWN_TOOL",
                "message": "Tool is not allowed",
            },
        }

    if not isinstance(arguments, dict):
        return {
            "ok": False,
            "error": {
                "code": "INVALID_ARGUMENTS",
                "message": "Arguments must be a dictionary",
            },
        }

    a = arguments.get("a")
    b = arguments.get("b")

    if any(
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(value)
        for value in (a, b)
    ):
        return {
            "ok": False,
            "error": {
                "code": "INVALID_ARGUMENTS",
                "message": "a and b must be finite numbers",
            },
        }

    return {"ok": True, "result": TOOLS[name](a, b)}


def compare_results():
    """Compare dispatch results with independent expected values."""

    cases = [
        ("add", {"a": 2, "b": 3}, 5),
        ("multiply", {"a": 2, "b": 3}, 6),
    ]

    results = []

    for name, arguments, expected in cases:
        actual = dispatch(name, arguments)
        results.append({
            "tool": name,
            "expected": expected,
            "actual": actual.get("result"),
            "passed": actual.get("result") == expected,
        })

    return results


if __name__ == "__main__":
    print("Local typed tool dispatch mock")
    print(json.dumps(compare_results(), indent=2))
    print("No MCP server or external service was called.")
