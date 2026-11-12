import json

TOOLS = {
    "add": lambda a, b: a + b,
    "multiply": lambda a, b: a * b,
}


def dispatch(request, execution_log=None):
    if execution_log is None:
        execution_log = []

    if not isinstance(request, dict):
        return {"ok": False, "error": {"code": "INVALID_REQUEST"}}

    tool = request.get("tool")
    arguments = request.get("arguments")

    if not isinstance(tool, str) or tool not in TOOLS:
        return {"ok": False, "error": {"code": "UNKNOWN_TOOL"}}

    if not isinstance(arguments, dict) or set(arguments) != {"a", "b"}:
        return {"ok": False, "error": {"code": "INVALID_ARGUMENTS"}}

    a, b = arguments["a"], arguments["b"]

    # bool is a Python subclass of int, so reject it explicitly.
    if (
        isinstance(a, bool) or isinstance(b, bool)
        or not isinstance(a, (int, float))
        or not isinstance(b, (int, float))
    ):
        return {"ok": False, "error": {"code": "INVALID_ARGUMENTS"}}

    execution_log.append(tool)
    return {"ok": True, "result": TOOLS[tool](a, b)}


if __name__ == "__main__":
    log = []
    cases = [
        {"tool": "add", "arguments": {"a": 2, "b": 3}},
        {"tool": "multiply", "arguments": {"a": 2, "b": 3}},
        {"tool": "add", "arguments": {"a": 0, "b": 0}},
        {"tool": "multiply", "arguments": {"a": -2, "b": 3}},
        {"tool": "divide", "arguments": {"a": 2, "b": 3}},
        {"tool": "add", "arguments": {"a": "2", "b": 3}},
    ]
    results = [dispatch(case, log) for case in cases]
    print(json.dumps({"results": results, "executed_tools": log}, indent=2))
