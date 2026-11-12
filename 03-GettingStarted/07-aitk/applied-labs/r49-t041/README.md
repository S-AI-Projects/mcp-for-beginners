# R49-T041: Local Server Configuration Validation

## Purpose

This applied lab demonstrates how a client validates a local MCP server-launch configuration before attempting to connect to a server.

This is a local mock simulation. It does not launch a process, start an MCP server, connect to Microsoft Foundry, or call an AI model.

## Prerequisites

- Python 3
- A local checkout of this repository
- No external packages or credentials required

## Configuration fixture

```python
{
    "command": "python",
    "args": ["server.py", "--port", "8080"],
    "env": {
        "API_KEY": "sample-secret",
        "PORT": "8080"
    }
}
```

## Run the example

From the repository root:

```bash
python3 03-GettingStarted/07-aitk/applied-labs/r49-t041/example.py
```

Expected output:

```text
Mock configuration validation successful
Command: python
Arguments: ['server.py', '--port', '8080']
Environment keys: ['API_KEY', 'PORT']
No server process was started.
```

Environment values are deliberately excluded from the summary.

## Validation rules

- A missing, empty, or whitespace-only command is rejected.
- Arguments must be a list of strings. A single string is rejected.
- An empty argument list is allowed.
- Environment configuration must be a dictionary with non-empty string keys and string values.
- The returned summary contains environment key names, never their values.
- Invalid configurations raise ValueError.

## Run the tests

```bash
python3 -m unittest discover -s 03-GettingStarted/07-aitk/applied-labs/r49-t041 -p "test_*.py"
```

The test suite covers valid input, missing and empty commands, invalid argument types, empty arguments, and environment-value redaction.

## Scope and limitations

This is a mock configuration validator, not a real MCP client or server launcher. It demonstrates basic input validation, argument boundaries, and secret redaction before a hypothetical launch.

It does not verify that an executable exists, that a server file exists, that environment variables work in a real process, or that an MCP connection succeeds. No process is launched and no external service is contacted.
