# R49-T048: Local Trace Aggregation Experiment

## Goal

Group local trace events by request ID and report duration, tool-call count, and request status without including prompt contents.

## Run

From the repository root:

    python3 11-MCPServerHandsOnLabs/11-Monitoring/applied-labs/r49-t048/example.py

## Expected core results

- Request A: 2 tool calls, 12 ms, success.
- Request B: failure.
- Request C: incomplete, with duration `null` because its end event is missing.

The program also compares three controlled input sizes: 0, 100, and 1,000 extra requests. It reports input event count, correctness, and observed aggregation time.

## Tests

    python3 -m unittest discover -s 11-MCPServerHandsOnLabs/11-Monitoring/applied-labs/r49-t048 -p "test_*.py" -v

## Trade-off and limitations

The experiment measures local aggregation time for small synthetic fixtures. Larger inputs contain more events and require more processing. Timings vary between runs and machines.

This is a Python simulation using in-memory events, not live OpenTelemetry traces, Application Insights, a deployed MCP server, or a real production performance benchmark. Prompt contents are deliberately excluded from summaries.
