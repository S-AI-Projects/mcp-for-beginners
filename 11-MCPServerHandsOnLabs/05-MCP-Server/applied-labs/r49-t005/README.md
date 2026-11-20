# R49-T005: Typed Tool Dispatch — Offline Service Adapter

## Objective

Demonstrate safe local tool dispatch using an explicit allowlist, argument validation, and a callable service adapter.

## Prerequisites

- Python 3
- No external dependencies
- Local repository checkout

## Files

- `example.py` — Tool dispatcher and deterministic local adapter.
- `test_example.py` — Automated unit tests.

## Run the Example

From the repository root:

```bash
python3 11-MCPServerHandsOnLabs/05-MCP-Server/applied-labs/r49-t005/example.py
```

## Expected Output

```text
{'success': True, 'result': 5}
{'success': True, 'result': 6}
{'success': False, 'error': {'code': 'UNKNOWN_TOOL', 'message': 'Tool is not allowed.'}}
{'success': False, 'error': {'code': 'INVALID_ARGUMENT_TYPE', 'message': 'Arguments a and b must be numbers.'}}
```

## Run Tests

```bash
python3 -m unittest discover -s 11-MCPServerHandsOnLabs/05-MCP-Server/applied-labs/r49-t005 -p "test_*.py" -v
```

## Scope and Limitations

This example uses a deterministic local mock adapter. It demonstrates allowlisted tool selection, numeric argument validation, structured errors, and callable dependency injection.

It does not implement MCP transport, connect to a real external service, or establish cloud-service, hardware, or trained-model behaviour. Those require separate real-service integration and testing.
