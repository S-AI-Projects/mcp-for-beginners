# R49-T044: Typed Tool Dispatch — Offline Service Adapter

## Goal

Demonstrate local tool dispatch through an explicit allowlist and a callable adapter.

## Implementation

The example supports two tools:

- `add(a, b)` returns the sum.
- `multiply(a, b)` returns the product.

The local adapter validates tool names and numeric arguments. Invalid requests return structured errors.

## Run

From the repository root:

    python3 06-CommunityContributions/applied-labs/r49-t044/example.py

## Expected results

- `add(2, 3)` returns `5`.
- `multiply(2, 3)` returns `6`.
- Unknown tools return an `invalid_tool_call` error.
- String arguments return an `invalid_tool_call` error.

## Tests

Run:

    python3 -m unittest discover -s 06-CommunityContributions/applied-labs/r49-t044 -p "test_*.py" -v

Seven tests cover normal, boundary, and failure cases.

## Fixture and limitations

This is a deterministic local Python mock. The callable adapter represents the external dependency boundary.

It does not establish real MCP transport behavior, network communication, authentication, remote service availability, or production server compatibility. No external service or model is used.