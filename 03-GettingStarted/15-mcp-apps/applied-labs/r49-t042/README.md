# R49-T042: Typed Tool Dispatch

## Goal
Build a local mock that dispatches typed tool calls using an explicit allowlist.

## Tools
- add(a, b): returns the sum.
- multiply(a, b): returns the product.

## Validation
The dispatcher checks that:
- The requested tool is allowed.
- Arguments are provided as a dictionary.
- Both a and b are finite numbers.
- Strings, booleans, missing values, and invalid numbers are rejected.

Errors use a structured format with an error code and message.

## Comparison

| Tool | Input | Expected |
|---|---|---:|
| add | 2, 3 | 5 |
| multiply | 2, 3 | 6 |

## Run
python3 03-GettingStarted/15-mcp-apps/applied-labs/r49-t042/example.py

## Tests
python3 -m unittest discover -s 03-GettingStarted/15-mcp-apps/applied-labs/r49-t042 -p "test_*.py"

## Limitations
This is a local Python mock. It does not start an MCP server, use MCP transport, connect to external services, or implement the complete MCP protocol.
