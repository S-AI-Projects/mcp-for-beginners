"""Validate a local server-launch configuration without starting a process."""


def validate_config(config):
    """Validate a launch configuration and return a redacted summary."""

    if not isinstance(config, dict):
        raise ValueError("Configuration must be a dictionary")

    command = config.get("command")
    if not isinstance(command, str) or not command.strip():
        raise ValueError("A non-empty command is required")

    args = config.get("args")
    if not isinstance(args, list):
        raise ValueError("Arguments must be a list")

    if not all(isinstance(arg, str) for arg in args):
        raise ValueError("Every argument must be a string")

    env = config.get("env", {})
    if not isinstance(env, dict):
        raise ValueError("Environment must be a dictionary")

    if not all(
        isinstance(key, str) and key.strip()
        for key in env
    ):
        raise ValueError("Environment keys must be non-empty strings")

    if not all(isinstance(value, str) for value in env.values()):
        raise ValueError("Environment values must be strings")

    return {
        "command": command,
        "args": args,
        "environment_keys": sorted(env.keys()),
    }


if __name__ == "__main__":
    sample_config = {
        "command": "python",
        "args": ["server.py", "--port", "8080"],
        "env": {
            "API_KEY": "sample-secret",
            "PORT": "8080",
        },
    }

    summary = validate_config(sample_config)

    print("Mock configuration validation successful")
    print("Command:", summary["command"])
    print("Arguments:", summary["args"])
    print("Environment keys:", summary["environment_keys"])
    print("No server process was started.")
