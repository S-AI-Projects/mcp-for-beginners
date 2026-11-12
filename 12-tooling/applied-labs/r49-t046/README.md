# R49-T046: Client Configuration Validation

## Goal

Validate a local server-launch configuration without starting a process.

## Example input

    {
      "command": "python",
      "args": ["server.py", "--port", "8080"],
      "env": {
        "API_KEY": "demo-secret",
        "PORT": "8080"
      }
    }

## Expected output

    {
      "command": "python",
      "args": ["server.py", "--port", "8080"],
      "env": {
        "API_KEY": "[REDACTED]",
        "PORT": "[REDACTED]"
      }
    }

The example also prints that no process was launched.

## Run

From the repository root:

    python3 12-tooling/applied-labs/r49-t046/example.py

## Tests

    python3 -m unittest discover -s 12-tooling/applied-labs/r49-t046 -p "test_*.py" -v

The tests cover valid configuration, missing and empty commands, invalid argument types, secret redaction and equivalence between the baseline and refactored implementations.

## Refactoring

The baseline implementation performed environment redaction inline. The refactored implementation extracts that responsibility into `redact_environment`. Both implementations are compared on the same fixture.

## Scope and limitations

This is a local Python simulation. It validates configuration shape only. It does not launch a server, verify that an executable or server file exists, connect to MCP, or validate real credentials. Environment values are never included in the returned summary.
