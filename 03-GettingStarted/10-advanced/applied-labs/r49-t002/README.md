
# R49-T002: Typed Tool Dispatch

## Objective

Demonstrate local tool dispatch through an explicit allowlist with numeric argument validation and structured errors.

This fixture extends the Advanced Server Usage lesson by demonstrating tool lookup, argument validation, handler execution, and failure handling.

## Prerequisites

- Python 3 standard library
- A local repository checkout
- Python 3

No model download, paid provider, GPU, hardware, or external service is required.

## Files

- `example.py` - Local tool dispatcher.
- `test_example.py` - Automated tests.

## Available tools

| Tool | Arguments | Expected result |
|---|---|---|
| add | a=2, b=3 | 5 |
| multiply | a=2, b=3 | 6 |

## Example invocation

Run from the repository root:

```bash
python3 03-GettingStarted/10-advanced/applied-labs/r49-t002/example.py
```

Expected output:

```json
{"ok": true, "result": 5}
{"ok": true, "result": 6}
{"ok": false, "error": {"code": "unknown_tool"}}
{"ok": false, "error": {"code": "invalid_arguments"}}
```

## Boundary and invalid cases

- Zero and negative numeric arguments are accepted.
- Integer and floating-point arguments are accepted.
- Boolean values are rejected even though Python treats bool as a subclass of int.
- Strings, missing arguments, extra arguments and non-finite numbers are rejected.
- Unknown tool names return a structured error.
- A failed lookup does not execute another registered tool.

The argument schema requires exactly two keys: `a` and `b`.

## Run tests

From the repository root:

```bash
python3 -m unittest discover -s 03-GettingStarted/10-advanced/applied-labs/r49-t002 -p "test_*.py" -v
```

## Scope and limitations

This is a local contract fixture that simulates tool dispatch.

It demonstrates an explicit allowlist, argument validation, local handler execution, and structured error responses.

It is not a full Model Context Protocol transport implementation. It does not establish real hardware, cloud service, or trained-model behavior.
