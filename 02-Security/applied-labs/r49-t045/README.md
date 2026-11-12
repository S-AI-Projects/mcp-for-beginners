# R49-T045: Request Authentication Boundary

## Goal

Demonstrate local bearer-token authentication using an injected verifier.

## Authentication cases

| Input | Expected result |
|---|---|
| Missing token | unauthenticated |
| Unknown token | invalid |
| Known token | authenticated, subject: student-001 |

## Run

From the repository root:

    python3 02-Security/applied-labs/r49-t045/example.py

## Tests

    python3 -m unittest discover -s 02-Security/applied-labs/r49-t045 -p "test_*.py" -v

Five tests cover missing, invalid and valid tokens, verifier injection and token redaction.

## Fixture and limitations

This example uses a local mock verifier and a demonstration token. It does not implement OAuth, token signatures, expiry, issuer or audience validation, or real MCP authentication. Token values are never included in log messages.