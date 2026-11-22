# R49-T009 Experiment Evidence

## Environment
- Python: 3.15.2
- Git: 2.54.0 (Apple Git-157)
- OS: macOS Darwin 27.2.0
- Architecture: ARM64

## Experiment
Local mock MCP client-configuration validation.

| Configuration | Arguments | Environment keys | Expected | Actual |
|---|---:|---:|---|---|
| Small | 1 | 1 | PASS | PASS |
| Medium | 3 | 2 | PASS | PASS |
| Large | 5 | 4 | PASS | PASS |

## Observations
All three configurations passed validation.
Environment variable values were redacted.
No process was launched.

Larger configurations contain more fields and produce
larger summaries. This experiment evaluates validation
correctness, not real-world performance.

## Automated tests
Command:
python3 -m unittest discover -s 03-GettingStarted/12-mcp-hosts/applied-labs/r49-t009 -p "test_*.py"

Result: 9 tests passed.

## Failure scenario
An empty command raised:
ValueError: A non-empty command is required

The invalid configuration was correctly rejected.

## Limitations
- Local mock fixtures only.
- No actual MCP host integration.
- No server process launched.
- No hardware or model performance claims.
