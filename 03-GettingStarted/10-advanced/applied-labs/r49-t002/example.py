"""Local typed tool-dispatch example for R49-T002."""

import json
import math


def add(a, b):
    return a + b


def multiply(a, b):
    return a * b


# Explicit allowlist: only these tools can be called.
TOOLS = {
    "add": add,
    "multiply": multiply,
}


def dispatch(request):
    if not isinstance(request, dict):
        return {"ok": False, "error": {"code": "invalid_request"}}

    tool_name = request.get("tool")
    arguments = request.get("arguments")

    if not isinstance(tool_name, str) or tool_name not in TOOLS:
        return {"ok": False, "error": {"code": "unknown_tool"}}

    if not isinstance(arguments, dict):
        return {"ok": False, "error": {"code": "invalid_arguments"}}

    if set(arguments.keys()) != {"a", "b"}:
        return {"ok": False, "error": {"code": "invalid_arguments"}}

    a = arguments["a"]
    b = arguments["b"]

    # bool is a subclass of int in Python, so reject it explicitly.
    if (
        isinstance(a, bool)
        or isinstance(b, bool)
        or not isinstance(a, (int, float))
        or not isinstance(b, (int, float))
    ):
        return {"ok": False, "error": {"code": "invalid_arguments"}}

    if not math.isfinite(a) or not math.isfinite(b):
        return {"ok": False, "error": {"code": "invalid_arguments"}}

    try:
        result = TOOLS[tool_name](a, b)
        return {"ok": True, "result": result}
    except Exception:
        return {"ok": False, "error": {"code": "tool_execution_failed"}}


if __name__ == "__main__":
    examples = [
        {"tool": "add", "arguments": {"a": 2, "b": 3}},
        {"tool": "multiply", "arguments": {"a": 2, "b": 3}},
        {"tool": "divide", "arguments": {"a": 2, "b": 3}},
        {"tool": "add", "arguments": {"a": "hello", "b": 3}},
    ]

    for example in examples:
        print(json.dumps(dispatch(example)))