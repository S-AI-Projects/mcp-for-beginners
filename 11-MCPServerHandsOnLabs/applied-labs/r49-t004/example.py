
import json
from math import isfinite


class ToolDispatcher:
    """Local simulation of allowlisted tool dispatch."""

    def __init__(self):
        self.tools = {
            "add": lambda a, b: a + b,
            "multiply": lambda a, b: a * b,
        }
        self.execution_log = []

    def dispatch_json(self, raw_json):
        trace = ["request_received"]

        try:
            request = json.loads(raw_json)
        except (json.JSONDecodeError, TypeError):
            trace.append("request_rejected")
            return {
                "ok": False,
                "error": {
                    "code": "INVALID_JSON",
                    "message": "Request must be valid JSON."
                },
                "trace": trace,
            }

        if not isinstance(request, dict):
            trace.append("request_rejected")
            return {
                "ok": False,
                "error": {
                    "code": "INVALID_REQUEST",
                    "message": "Request must be a JSON object."
                },
                "trace": trace,
            }

        trace.append("request_parsed")

        tool_name = request.get("tool")
        arguments = request.get("arguments")

        if tool_name not in self.tools:
            trace.append("tool_rejected")
            return {
                "ok": False,
                "error": {
                    "code": "UNKNOWN_TOOL",
                    "message": "Tool is not in the allowlist."
                },
                "trace": trace,
            }

        trace.append("tool_allowed")

        if not isinstance(arguments, dict):
            trace.append("arguments_rejected")
            return {
                "ok": False,
                "error": {
                    "code": "INVALID_ARGUMENTS",
                    "message": "Arguments must be a JSON object."
                },
                "trace": trace,
            }

        if set(arguments) != {"a", "b"}:
            trace.append("arguments_rejected")
            return {
                "ok": False,
                "error": {
                    "code": "INVALID_ARGUMENTS",
                    "message": "Exactly two arguments, a and b, are required."
                },
                "trace": trace,
            }

        a = arguments["a"]
        b = arguments["b"]

        valid_numbers = all(
            type(value) in (int, float)
            and (type(value) is int or isfinite(value))
            for value in (a, b)
        )

        if not valid_numbers:
            trace.append("arguments_rejected")
            return {
                "ok": False,
                "error": {
                    "code": "INVALID_ARGUMENTS",
                    "message": "Arguments a and b must be finite numbers."
                },
                "trace": trace,
            }

        trace.append("arguments_validated")
        self.execution_log.append(tool_name)
        result = self.tools[tool_name](a, b)
        trace.append("tool_executed")
        trace.append("result_recorded")

        return {
            "ok": True,
            "result": result,
            "trace": trace,
        }


if __name__ == "__main__":
    dispatcher = ToolDispatcher()

    examples = [
        {"tool": "add", "arguments": {"a": 2, "b": 3}},
        {"tool": "multiply", "arguments": {"a": 2, "b": 3}},
        {"tool": "divide", "arguments": {"a": 2, "b": 3}},
        {"tool": "add", "arguments": {"a": "2", "b": 3}},
    ]

    for example in examples:
        print(json.dumps(
            dispatcher.dispatch_json(json.dumps(example)),
            indent=2
        ))
