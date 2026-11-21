"""Validate a local server configuration without launching a process."""

from typing import Any


def validate_config(config: dict[str, Any]) -> dict[str, Any]:
    """Validate command, arguments and environment keys."""

    if not isinstance(config, dict):
        raise ValueError("Configuration must be a dictionary")

    command = config.get("command")

    if not isinstance(command, str) or not command.strip():
        raise ValueError("A valid command is required")

    args = config.get("args")

    if not isinstance(args, list):
        raise ValueError("Arguments must be an array")

    if not all(isinstance(arg, str) for arg in args):
        raise ValueError("Every argument must be a string")

    env = config.get("env", {})

    if not isinstance(env, dict):
        raise ValueError("Environment must be a dictionary")

    if not all(isinstance(key, str) and key for key in env):
        raise ValueError("Environment keys must be non-empty strings")

    return {
        "valid": True,
        "command": command,
        "args": args,
        "env": {key: "[REDACTED]" for key in env},
        "process_launched": False,
    }


if __name__ == "__main__":
    example_config = {
        "command": "python3",
        "args": ["server.py", "--port", "8000"],
        "env": {
            "API_KEY": "example-secret",
            "SERVER_MODE": "development",
        },
    }

    print(validate_config(example_config))