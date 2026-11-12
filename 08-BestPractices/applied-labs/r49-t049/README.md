# R49-T049: Typed Tool Dispatch — Boundary Cases

## Goal

Dispatch local JSON requests to two explicitly allowed tools: `add(a, b)` and `multiply(a, b)`. Validate tool names and arguments before executing anything.

## Run

From the repository root:

```bash
python3 08-BestPractices/applied-labs/r49-t049/example.py
python3 -m unittest discover -s 08-BestPractices/applied-labs/r49-t049 -p "test_*.py" -v
```

## Expected behavior

| Request | Expected result |
|---|---|
| `add(2, 3)` | `5` |
| `multiply(2, 3)` | `6` |
| `add(0, 0)` | `0` |
| `multiply(-2, 3)` | `-6` |
| Unknown tool `divide` | `UNKNOWN_TOOL` |
| String argument `"2"` | `INVALID_ARGUMENTS` |
| Boolean argument `true` | `INVALID_ARGUMENTS` |
| Missing argument | `INVALID_ARGUMENTS` |

## Boundary decision

Zero and negative numbers are valid numeric inputs. Integers and floats are accepted. Strings and booleans are rejected. Python treats `bool` as a subclass of `int`, so booleans are explicitly rejected.

Arguments are validated before a tool is executed. Invalid calls do not enter the execution log, and a later valid call can still succeed.

## Scope and limitations

This is a local contract example. It does not implement MCP transport, JSON-RPC, a live server, authentication, or external tool execution.