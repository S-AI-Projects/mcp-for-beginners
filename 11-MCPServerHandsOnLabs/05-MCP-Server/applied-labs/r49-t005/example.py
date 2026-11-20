
"""R49-T005: Typed tool dispatch with a local service adapter."""

import json


def add(a, b):
    return a + b


def multiply(a, b):
    return a * b


class LocalServiceAdapter:
    """Deterministic local substitute for an external service."""

    def __init__(self):
        self.tools = {
            "add": add,
            "multiply": multiply,
        }
        self.execution_log = []

    def __call__(self, tool_name, arguments):
        self.execution_log.append(tool_name)
        return self.tools[tool_name](arguments["a"], arguments["b"])


class ToolDispatcher:
    """Validates JSON requests and dispatches allowlisted tools."""

    ALLOWED_TOOLS = {"add", "multiply"}

    def __init__(self, service):
        self.service = service

    def dispatch(self, raw_json):
        try:
            request = json.loads(raw_json)
        except (json.JSONDecodeError, TypeError):
            return self.error("INVALID_JSON", "Request must be valid JSON.")

        if not isinstance(request, dict):
            return self.error("INVALID_REQUEST", "Request must be an object.")

        if set(request) != {"tool", "arguments"}:
            return self.error(
                "INVALID_REQUEST",
                "Request must contain tool and arguments."
            )

        tool_name = request["tool"]
        arguments = request["arguments"]

        if not isinstance(tool_name, str) or tool_name not in self.ALLOWED_TOOLS:
            return self.error("UNKNOWN_TOOL", "Tool is not allowed.")

        if not isinstance(arguments, dict) or set(arguments) != {"a", "b"}:
            return self.error(
                "INVALID_ARGUMENTS",
                "Arguments must contain exactly a and b."
            )

        a = arguments["a"]
        b = arguments["b"]

        if any(
            isinstance(value, bool) or not isinstance(value, (int, float))
            for value in (a, b)
        ):
            return self.error(
                "INVALID_ARGUMENT_TYPE",
                "Arguments a and b must be numbers."
            )

        try:
            result = self.service(tool_name, arguments)
        except Exception:
            return self.error("EXECUTION_ERROR", "Tool execution failed.")

        return {"success": True, "result": result}

    @staticmethod
    def error(code, message):
        return {
            "success": False,
            "error": {
                "code": code,
                "message": message,
            },
        }


def main():
    service = LocalServiceAdapter()
    dispatcher = ToolDispatcher(service)

    requests = [
        '{"tool": "add", "arguments": {"a": 2, "b": 3}}',
        '{"tool": "multiply", "arguments": {"a": 2, "b": 3}}',
        '{"tool": "divide", "arguments": {"a": 2, "b": 3}}',
        '{"tool": "add", "arguments": {"a": "2", "b": 3}}',
    ]

    for request in requests:
        print(dispatcher.dispatch(request))


if __name__ == "__main__":
    main()

