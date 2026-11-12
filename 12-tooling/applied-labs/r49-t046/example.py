def validate_baseline(config):
    """Original implementation before extracting the redaction helper."""
    command = config.get("command")
    args = config.get("args")
    env = config.get("env")

    if not isinstance(command, str) or not command.strip():
        raise ValueError("command must be a non-empty string")

    if not isinstance(args, list) or not all(isinstance(x, str) for x in args):
        raise ValueError("args must be a list of strings")

    if not isinstance(env, dict) or not all(
        isinstance(key, str) and key for key in env
    ):
        raise ValueError("env must be a dictionary with named keys")

    return {
        "command": command,
        "args": args,
        "env": {key: "[REDACTED]" for key in env},
    }


def redact_environment(env):
    """Extracted responsibility: hide environment variable values."""
    return {key: "[REDACTED]" for key in env}


def validate_configuration(config):
    """Refactored implementation with the same validation contract."""
    command = config.get("command")
    args = config.get("args")
    env = config.get("env")

    if not isinstance(command, str) or not command.strip():
        raise ValueError("command must be a non-empty string")

    if not isinstance(args, list) or not all(isinstance(x, str) for x in args):
        raise ValueError("args must be a list of strings")

    if not isinstance(env, dict) or not all(
        isinstance(key, str) and key for key in env
    ):
        raise ValueError("env must be a dictionary with named keys")

    return {
        "command": command,
        "args": args,
        "env": redact_environment(env),
    }


if __name__ == "__main__":
    fixture = {
        "command": "python",
        "args": ["server.py", "--port", "8080"],
        "env": {"API_KEY": "demo-secret", "PORT": "8080"},
    }
    print("Validated configuration:")
    print(validate_configuration(fixture))
    print("No process was launched.")
