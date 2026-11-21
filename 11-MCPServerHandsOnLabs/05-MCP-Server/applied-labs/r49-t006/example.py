"""Local typed tool-dispatch teaching example."""

import math


def add(a, b):
    return a + b


def multiply(a, b):
    return a * b


TOOL_ALLOWLIST = {
    "add": add,
    "multiply": multiply,
}


def validate_arguments(arguments):
    """Validate exactly two finite numeric arguments."""
    if not isinstance(arguments, dict):
        return False

    if set(arguments) != {"a", "b"}:
        return False

    for value in arguments.values():
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return False
        if not math.isfinite(value):
            return False

    return True


def dispatch(tool_name, arguments):
    """Dispatch only explicitly allowed tools."""

    if not isinstance(tool_name, str) or tool_name not in TOOL_ALLOWLIST:
        return {
            "ok": False,
            "error": {
                "code": "unknown_tool",
                "message": "Tool is not in the allowlist.",
            },
        }

    if not validate_arguments(arguments):
        return {
            "ok": False,
            "error": {
                "code": "invalid_arguments",
                "message": "Expected numeric arguments 'a' and 'b'.",
            },
        }

    result = TOOL_ALLOWLIST[tool_name](arguments["a"], arguments["b"])

    return {"ok": True, "result": result}


if __name__ == "__main__":
    print(dispatch("add", {"a": 2, "b": 3}))
    print(dispatch("multiply", {"a": 2, "b": 3}))
    print(dispatch("divide", {"a": 2, "b": 3}))
    print(dispatch("add", {"a": "2", "b": 3}))