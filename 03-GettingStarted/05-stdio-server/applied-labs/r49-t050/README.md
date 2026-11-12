# R49-T050: Newline-Delimited Message Framing

## Goal

Demonstrate how a local program reads newline-delimited JSON messages, preserves request IDs, reports malformed messages, and keeps diagnostics separate from protocol output.

## Concepts

- Each non-empty line is parsed as an independent JSON message.
- Valid JSON objects are returned with their original request IDs unchanged.
- Malformed JSON produces a structured `PARSE_ERROR` result containing the line number.
- Valid JSON that is not an object produces `INVALID_MESSAGE`.
- Blank lines are ignored.
- Diagnostic details are written to stderr; structured results are written to stdout.

## Run the example

From the repository root:

```bash
printf '%s\n' '{"jsonrpc":"2.0","id":1,"method":"ping"}' '{"jsonrpc":"2.0","id":2,"method":"ping"}' | python3 03-GettingStarted/05-stdio-server/applied-labs/r49-t050/example.py