# R49-T013: Client-Configuration Validation — Compare Two Approaches

## Purpose & Lesson Connection

In "🚀 MCP Tooling" (`12-tooling`), developer tooling integrates MCP servers to automate tasks and run tools. To launch servers reliably, tools must validate the configuration records before executing child processes.

This lab implements and validates server launch configurations and focuses on **comparing two independent verification approaches**:
1. **Direct Implementation**: Imperative validation with early-exit exception throwing.
2. **Reference Table / Independent Check**: Declarative property verification evaluated against an explicit benchmark table.

Both approaches consume identical inputs, enforce identical boundary contracts, and produce identical redacted outputs.

## Boundary Decisions

- Missing, empty, or whitespace command fails.
- Single string argument fails (must be an explicit array).
- Sensitive environment variable values are redacted from output; only variable names are exposed.
- No child processes are launched.

## Running the Example

```bash
python3 12-tooling/applied-labs/r49-t013/example.py
```

### Expected Output

```text
=== MCP Tooling: Client-Configuration Validation (R49-T013) ===
Case [valid_standard]: AGREED (success=True)
   Redacted Output: {'command': 'python', 'args': ['server.py', '--debug'], 'environment_keys': ['ENV', 'SECRET_KEY']}
Case [valid_minimal]: AGREED (success=True)
   Redacted Output: {'command': 'node', 'args': [], 'environment_keys': []}
Case [invalid_missing_command]: AGREED (success=False)
Case [invalid_single_string_args]: AGREED (success=False)

All cases compared with identical inputs. Secret values were completely redacted.
No child processes were launched.
```

## Running the Unit Tests

```bash
python3 -m unittest discover -s 12-tooling/applied-labs/r49-t013 -p "test_*.py"
```

## Scope and Limitations

This is a local comparison and validation experiment. It does not invoke system executables, start server processes, or communicate with external services.
