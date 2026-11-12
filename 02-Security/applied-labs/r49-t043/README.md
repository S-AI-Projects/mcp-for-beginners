# R49-T043: Request Authentication Boundary

## Objective

Demonstrate a local bearer-token authentication boundary using an injected verifier.

## Authentication outcomes

| Input | Verification | Output |
|---|---|---|
| Missing token | Missing | `unauthenticated` |
| Unknown token | Rejected | `invalid` |
| Known token | Valid | Subject (`student-01`) |

## Implementation

The example uses a small local token fixture and an injected verifier function.

It records intermediate states:
1. Whether a token was supplied.
2. The verification result.
3. The resulting identity.
4. The final output.

An invariant checks that the final output agrees with the verification state. Token values are never included in logs.

## Run the example

```bash
python3 02-Security/applied-labs/r49-t043/example.py
```

## Run tests

```bash
python3 -m unittest discover -s 02-Security/applied-labs/r49-t043 -p "test_*.py" -v
```

## Simplifications and limitations

This is a local educational simulation. It does not implement OAuth, JWT signature verification, token expiry, network authentication, or a production MCP server. The fixture verifier represents an external verification boundary.

## Lesson connection

This lab demonstrates the authentication and secure token management principles discussed in the MCP Security lesson. It shows why identity must be established through verification rather than simply trusting a supplied token.