# R49-T012: Client-Configuration Validation (Boundary-Case Lesson Extension)

## Purpose & Lesson Connection

In "Setting Up Popular MCP Host Clients" (`03-GettingStarted/12-mcp-hosts`), host applications (such as Claude Desktop, VS Code, or Cursor) manage configuration files specifying how to launch local MCP servers via standard I/O.

Before spawning any child process, host software must validate the configuration record:
1. Ensure the executable command is specified and non-empty.
2. Require an explicit array of arguments (rejecting a raw string to prevent shell injection or word-splitting bugs).
3. Safely redact sensitive environment variable values when generating logs or diagnostic reports.

This applied lab implements and verifies these validation rules and boundary decisions using local fixtures.

## Boundary Decisions

- **Smallest Valid Case**: `{"command": "python"}`. When omitted, `args` defaults to an empty list `[]` and `env` defaults to an empty dictionary `{}`.
- **Boundary Case**: `{"command": "uv", "args": [], "env": {}}`. Explicit empty collections are valid.
- **Argument Rejection Policy**: Passing a single string (`"args": "server.js"`) is rejected. Hosts require an explicit array of tokens so that arguments are passed directly via `execve` without shell interpretation.
- **Secret Redaction**: Environment values (e.g. API keys or tokens) are strictly omitted from the report. Only sorted environment key names are returned.

## Prerequisites

- Python 3.8+ (standard library only)
- Local checkout of this repository
- No external packages or process privileges required

## Configuration Fixture

```python
{
    "command": "node",
    "args": ["build/index.js", "--port", "3000"],
    "env": {
        "API_KEY": "super-secret-token",
        "PORT": "3000"
    }
}
```

## Running the Example

From the repository root:

```bash
python3 03-GettingStarted/12-mcp-hosts/applied-labs/r49-t012/example.py
```

### Expected Output

```text
=== MCP Host Configuration Validation (R49-T012) ===
Normal config validated successfully:
  Command: node
  Args: ['build/index.js', '--port', '3000']
  Environment Keys: ['API_KEY', 'PORT']
  (Secret values were redacted)

Boundary config (empty args & env) validated successfully:
  Summary: {'command': 'python', 'args': [], 'environment_keys': []}

Testing invalid args (single string):
  Caught expected error: Arguments must be a list of strings, not a single string

Testing missing command:
  Caught expected error: A non-empty string 'command' is required

Demo completed successfully. No server process was launched.
```

## Running the Unit Tests

From the repository root:

```bash
python3 -m unittest discover -s 03-GettingStarted/12-mcp-hosts/applied-labs/r49-t012 -p "test_*.py"
```

## Scope and Limitations

This is a local configuration validator simulation. It does not verify executable presence on `$PATH`, does not start child processes, and does not establish live MCP connections.
