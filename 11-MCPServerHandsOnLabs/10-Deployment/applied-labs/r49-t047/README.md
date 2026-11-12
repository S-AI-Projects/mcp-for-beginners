# R49-T047: Tool Dispatch Failure and Recovery

## Goal

Demonstrate local JSON tool dispatch using an explicit allowlist and numeric argument validation.

## Valid calls

- `add(2, 3)` returns `5`.
- `multiply(2, 3)` returns `6`.

## Failure and recovery

An unknown tool returns `UNKNOWN_TOOL`. A string argument such as `"2"` returns `INVALID_ARGUMENTS`. Neither failed call executes a tool.

A subsequent valid `multiply(2, 3)` call succeeds, demonstrating recovery.

## Run

From the repository root:

    python3 11-MCPServerHandsOnLabs/10-Deployment/applied-labs/r49-t047/example.py

## Tests

    python3 -m unittest discover -s 11-MCPServerHandsOnLabs/10-Deployment/applied-labs/r49-t047 -p "test_*.py" -v

## Scope and limitations

This is a local Python contract fixture. It uses an in-memory allowlist and does not implement MCP transport, network communication, authentication, deployment, or a production server.
