"""Typed tool dispatch with explicit allowlist and structured error envelopes.

Task R49-T017: Worked example with regression checks for Deployment Strategies.
"""

from typing import Any, Dict


ALLOWLIST = {"add", "multiply"}


def dispatch_tool(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Dispatch a JSON tool request through allowlist and numeric type validation.

    Parameters:
        payload: Dictionary containing 'tool' and 'arguments'.

    Returns:
        Structured response dictionary with 'success', and either 'result' or 'error'.
    """
    if not isinstance(payload, dict):
        return {
            "success": False,
            "error": {"code": "INVALID_PAYLOAD", "message": "Payload must be a dictionary"},
        }

    tool_name = payload.get("tool")
    if tool_name not in ALLOWLIST:
        return {
            "success": False,
            "error": {
                "code": "UNKNOWN_TOOL",
                "message": f"Tool '{tool_name}' is not in allowlist: {sorted(ALLOWLIST)}",
            },
        }

    args = payload.get("arguments")
    if not isinstance(args, dict):
        return {
            "success": False,
            "error": {"code": "INVALID_ARGUMENTS", "message": "Arguments must be a dictionary"},
        }

    if "a" not in args or "b" not in args:
        return {
            "success": False,
            "error": {"code": "MISSING_ARGUMENT", "message": "Arguments 'a' and 'b' are required"},
        }

    a, b = args["a"], args["b"]
    if isinstance(a, bool) or not isinstance(a, (int, float)):
        return {
            "success": False,
            "error": {
                "code": "INVALID_ARGUMENT_TYPE",
                "message": f"Argument 'a' must be numeric, got {type(a).__name__}",
            },
        }
    if isinstance(b, bool) or not isinstance(b, (int, float)):
        return {
            "success": False,
            "error": {
                "code": "INVALID_ARGUMENT_TYPE",
                "message": f"Argument 'b' must be numeric, got {type(b).__name__}",
            },
        }

    if tool_name == "add":
        return {"success": True, "tool": "add", "result": a + b}
    elif tool_name == "multiply":
        return {"success": True, "tool": "multiply", "result": a * b}

    return {
        "success": False,
        "error": {"code": "DISPATCH_FAILED", "message": f"Execution failed for {tool_name}"},
    }


def main() -> None:
    """Run demonstration with worked examples and error cases."""
    print("=== Typed Tool Dispatch (R49-T017) ===")

    # 1. Normal call: add(2, 3) -> 5
    res_add = dispatch_tool({"tool": "add", "arguments": {"a": 2, "b": 3}})
    print(f"add(2, 3) -> {res_add}")

    # 2. Normal call: multiply(2, 3) -> 6
    res_mul = dispatch_tool({"tool": "multiply", "arguments": {"a": 2, "b": 3}})
    print(f"multiply(2, 3) -> {res_mul}")

    # 3. Error case: unknown tool
    res_unk = dispatch_tool({"tool": "subtract", "arguments": {"a": 5, "b": 2}})
    print(f"unknown tool 'subtract' -> {res_unk}")

    # 4. Error case: string 'a'
    res_err_type = dispatch_tool({"tool": "add", "arguments": {"a": "2", "b": 3}})
    print(f"string argument a -> {res_err_type}")

    print("\nDemonstration complete. Failed calls return structured errors without executing other tools.")


if __name__ == "__main__":
    main()
