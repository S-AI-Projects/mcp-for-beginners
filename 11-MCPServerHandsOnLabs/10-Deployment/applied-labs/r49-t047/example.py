import json


def add(a, b):
    return a + b


def multiply(a, b):
    return a * b


TOOLS = {
    "add": add,
    "multiply": multiply,
}


def dispatch(request, execution_log=None):
    if execution_log is None:
        execution_log = []

    tool = request.get("tool")
    arguments = request.get("arguments")

    if tool not in TOOLS:
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
                "message": "Arguments must be an object",
            },
        }

    if set(arguments) != {"a", "b"}:
        return {
            "ok": False,
            "error": {
                "code": "INVALID_ARGUMENTS",
                "message": "Expected numeric arguments a and b",
            },
        }

    a = arguments["a"]
    b = arguments["b"]

    if (
        isinstance(a, bool) or isinstance(b, bool)
        or not isinstance(a, (int, float))
        or not isinstance(b, (int, float))
    ):
        return {
            "ok": False,
            "error": {
                "code": "INVALID_ARGUMENTS",
                "message": "Arguments a and b must be numbers",
            },
        }

    execution_log.append(tool)
    result = TOOLS[tool](a, b)

    return {"ok": True, "result": result}


if __name__ == "__main__":
    calls = [
        {"tool": "unknown", "arguments": {"a": 2, "b": 3}},
        {"tool": "add", "arguments": {"a": 2, "b": 3}},
        {"tool": "multiply", "arguments": {"a": 2, "b": 3}},
        {"tool": "add", "arguments": {"a": "2", "b": 3}},
    ]

    log = []
    for call in calls:
        print(json.dumps(dispatch(call, log)))

    print("Executed tools:", log)
