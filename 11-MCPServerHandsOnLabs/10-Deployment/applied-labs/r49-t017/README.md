# R49-T017: Typed Tool Dispatch — Worked Example with Checks

## Purpose & Lesson Connection

In "Deployment Strategies" (`11-MCPServerHandsOnLabs/10-Deployment`), production servers require deterministic dispatch mechanisms to prevent unexpected behavior and security regressions. An MCP server must enforce an explicit allowlist of exposed tools and validate JSON argument payloads before execution.

This applied lab demonstrates:
1. Dispatching `add(a, b)` and `multiply(a, b)` through an explicit allowlist.
2. Numeric argument validation (`add(2, 3)` $\rightarrow$ 5, `multiply(2, 3)` $\rightarrow$ 6).
3. Structured error responses for unknown tools or non-numeric arguments (such as string `a`).
4. Strict single-tool dispatch: a failed tool invocation terminates immediately and never executes a fallback or subsequent tool.

## Worked Examples

| Call Payload | Tool Name | Arguments | Outcome | Structured Return |
| :--- | :--- | :--- | :--- | :--- |
| `{"tool": "add", "arguments": {"a": 2, "b": 3}}` | `add` | `{"a": 2, "b": 3}` | Success | `{"success": True, "tool": "add", "result": 5}` |
| `{"tool": "multiply", "arguments": {"a": 2, "b": 3}}` | `multiply` | `{"a": 2, "b": 3}` | Success | `{"success": True, "tool": "multiply", "result": 6}` |
| `{"tool": "subtract", ...}` | `subtract` | N/A | Error | `{"success": False, "error": {"code": "UNKNOWN_TOOL", ...}}` |
| `{"tool": "add", "arguments": {"a": "2", "b": 3}}` | `add` | `a: "2"` (str) | Error | `{"success": False, "error": {"code": "INVALID_ARGUMENT_TYPE", ...}}` |

## Running the Example

From the repository root:

```bash
python3 11-MCPServerHandsOnLabs/10-Deployment/applied-labs/r49-t017/example.py
```

### Expected Output

```text
=== Typed Tool Dispatch (R49-T017) ===
add(2, 3) -> {'success': True, 'tool': 'add', 'result': 5}
multiply(2, 3) -> {'success': True, 'tool': 'multiply', 'result': 6}
unknown tool 'subtract' -> {'success': False, 'error': {'code': 'UNKNOWN_TOOL', 'message': "Tool 'subtract' is not in allowlist: ['add', 'multiply']"}}
string argument a -> {'success': False, 'error': {'code': 'INVALID_ARGUMENT_TYPE', 'message': "Argument 'a' must be numeric, got str"}}

Demonstration complete. Failed calls return structured errors without executing other tools.
```

## Running the Unit Tests

```bash
python3 -m unittest discover -s 11-MCPServerHandsOnLabs/10-Deployment/applied-labs/r49-t017 -p "test_*.py"
```

## Scope and Limitations

This is a local contract fixture demonstrating allowlist filtering and argument validation. It does not implement full MCP JSON-RPC wire protocols or network transports.
