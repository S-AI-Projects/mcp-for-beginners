import json


def add(a, b):
    return a + b


def multiply(a, b):
    return a * b


TOOLS = {
    "add": add,
    "multiply": multiply,
}


def local_adapter(tool_name, arguments):
    """Local mock adapter for deterministic tool execution."""
    if tool_name not in TOOLS:
        raise ValueError("Unknown tool")

    if not isinstance(arguments, dict):
        raise ValueError("Arguments must be an object")

    if set(arguments) != {"a", "b"}:
        raise ValueError("Expected exactly arguments a and b")

    a = arguments["a"]
    b = arguments["b"]

    if (
        isinstance(a, bool)
        or isinstance(b, bool)
        or not isinstance(a, (int, float))
        or not isinstance(b, (int, float))
    ):
        raise ValueError("Arguments a and b must be numbers")

    return TOOLS[tool_name](a, b)


def dispatch_tool(tool_name, arguments, adapter=local_adapter):
    try:
        result = adapter(tool_name, arguments)
        return {"ok": True, "result": result}
    except (ValueError, TypeError) as error:
        return {
            "ok": False,
            "error": {
                "type": "invalid_tool_call",
                "message": str(error),
            },
        }


if __name__ == "__main__":
    calls = [
        {"tool": "add", "arguments": {"a": 2, "b": 3}},
        {"tool": "multiply", "arguments": {"a": 2, "b": 3}},
        {"tool": "divide", "arguments": {"a": 2, "b": 3}},
        {"tool": "add", "arguments": {"a": "2", "b": 3}},
    ]

    for call in calls:
        response = dispatch_tool(call["tool"], call["arguments"])
        print(json.dumps({
            "tool": call["tool"],
            **response,
        }))