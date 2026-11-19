"""Local JSON tool-dispatch fixture; not a full MCP transport."""

import json
import math
import sys


def add(a: int | float, b: int | float) -> int | float:
    return a + b


def multiply(a: int | float, b: int | float) -> int | float:
    return a * b


# Explicit tool allowlist
TOOL_ALLOWLIST = {
    "add": add,
    "multiply": multiply,
}


def dispatch(payload: str) -> dict:
    """Validate and dispatch one local JSON tool call."""

    try:
        request = json.loads(payload)
    except (json.JSONDecodeError, TypeError):
        return {
            "ok": False,
            "error": {
                "code": "invalid_json",
                "message": "Request must contain valid JSON.",
            },
        }

    if not isinstance(request, dict):
        return {
            "ok": False,
            "error": {
                "code": "invalid_request",
                "message": "Request must be a JSON object.",
            },
        }

    tool_name = request.get("tool")

    if tool_name not in TOOL_ALLOWLIST:
        return {
            "ok": False,
            "error": {
                "code": "unknown_tool",
                "message": "Tool is not allowed.",
            },
        }

    arguments = request.get("arguments")

    if not isinstance(arguments, dict):
        return {
            "ok": False,
            "error": {
                "code": "invalid_arguments",
                "message": "Arguments must be a JSON object.",
            },
        }

    if set(arguments) != {"a", "b"}:
        return {
            "ok": False,
            "error": {
                "code": "invalid_arguments",
                "message": "Exactly two arguments, a and b, are required.",
            },
        }

    a = arguments["a"]
    b = arguments["b"]

    for value in (a, b):
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return {
                "ok": False,
                "error": {
                    "code": "invalid_arguments",
                    "message": "Arguments a and b must be numbers.",
                },
            }

        if isinstance(value, float) and not math.isfinite(value):
            return {
                "ok": False,
                "error": {
                    "code": "invalid_arguments",
                    "message": "Arguments must be finite numbers.",
                },
            }

    result = TOOL_ALLOWLIST[tool_name](a, b)

    return {"ok": True, "result": result}


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(json.dumps({
            "ok": False,
            "error": {
                "code": "invalid_request",
                "message": "Provide one JSON request argument.",
            },
        }))
        sys.exit(1)

    response = dispatch(sys.argv[1])
    print(json.dumps(response))

    if not response["ok"]:
        sys.exit(1)
