
# R49-T006 — Typed Tool Dispatch

## Objective
Demonstrate local typed tool dispatch using an explicit allowlist and numeric argument validation.

## Implementation
- `example.py`: Contains the tool dispatcher and local fixtures.
- `test_example.py`: Contains automated unit tests.

## Prerequisites
- Python 3
- Local repository checkout
- No external API, GPU, model download, or hardware required.

## Run

From the repository root:

```bash
python3 11-MCPServerHandsOnLabs/05-MCP-Server/applied-labs/r49-t006/example.py
```

## Test

```bash
python3 -m unittest discover -s 11-MCPServerHandsOnLabs/05-MCP-Server/applied-labs/r49-t006 -p "test_*.py" -v
```

## Expected results

| Input | Expected result |
|---|---|
| add(2,3) | 5 |
| multiply(2,3) | 6 |
| Unknown tool | Structured error |
| String argument | Structured error |

## Scope and limitations

This is a local simulation of tool dispatch. It is not a complete MCP transport implementation and does not demonstrate real hardware, cloud services, or trained-model behavior.

## Verification

The test suite covers normal, boundary, failure, and before/after equivalence scenarios. An intentionally incorrect expected result was also used to verify that the test suite exits with failure.
