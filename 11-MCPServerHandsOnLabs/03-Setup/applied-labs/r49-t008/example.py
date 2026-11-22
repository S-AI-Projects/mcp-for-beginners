"""Local JSON fixture for typed tool dispatch and failure recovery."""

import json
import math


def add(a, b):
    return a + b


def multiply(a, b):
    return a * b


# Explicit allowlist: only these two tools can be dispatched.
TOOLS = {
    "add": add,
    "multiply": multiply,
}


def error(code, message):
    return {
        "ok": False,
        "error": {
            "code": code,
            "message": message,
        },
    }


def dispatch(request):
    """Validate a local request and dispatch only an allowlisted tool."""

    if not isinstance(request, dict):
        return error("INVALID_REQUEST", "Request must be a JSON object.")

    tool_name = request.get("tool")

    if not isinstance(tool_name, str):
        return error("INVALID_REQUEST", "Tool name must be a string.")

    if tool_name not in TOOLS:
        return error("UNKNOWN_TOOL", f"Tool '{tool_name}' is not allowed.")

    arguments = request.get("arguments")

    if not isinstance(arguments, dict):
        return error("INVALID_ARGUMENTS", "Arguments must be an object.")

    if set(arguments) != {"a", "b"}:
        return error(
            "INVALID_ARGUMENTS",
            "Exactly two arguments, 'a' and 'b', are required.",
        )

    for name in ("a", "b"):
        value = arguments[name]

        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
        ):
            return error(
                "INVALID_ARGUMENT",
                f"Argument '{name}' must be a finite number.",
            )

    # Dispatch happens only after every validation succeeds.
    result = TOOLS[tool_name](
        arguments["a"],
        arguments["b"],
    )

    return {
        "ok": True,
        "tool": tool_name,
        "result": result,
    }


def dispatch_json(raw_json):
    """Parse and dispatch one JSON request."""
    try:
        request = json.loads(raw_json)
    except (json.JSONDecodeError, TypeError):
        return error("INVALID_JSON", "Input must contain valid JSON.")

    return dispatch(request)


if __name__ == "__main__":
    fixtures = [
        '{"tool":"add","arguments":{"a":2,"b":3}}',
        '{"tool":"multiply","arguments":{"a":2,"b":3}}',
        '{"tool":"divide","arguments":{"a":2,"b":3}}',
        '{"tool":"add","arguments":{"a":"2","b":3}}',
        '{"tool":"multiply","arguments":{"a":2,"b":3}}',
    ]

    print("Local typed tool dispatch demonstration:")
    for fixture in fixtures:
        print(json.dumps(dispatch_json(fixture), sort_keys=True))
