
"""Local MCP launch configuration validation experiment.

This example validates configuration data only.
It never launches a process or connects to an MCP host.
"""


def validate_config(config):
    """Validate a launch configuration and return a redacted summary."""

    if not isinstance(config, dict):
        raise ValueError("Configuration must be a dictionary")

    command = config.get("command")
    if not isinstance(command, str) or not command.strip():
        raise ValueError("A non-empty command is required")

    if "args" not in config:
        raise ValueError("args must be provided")

    args = config["args"]
    if not isinstance(args, list):
        raise ValueError("args must be an array of strings")

    if not all(isinstance(arg, str) for arg in args):
        raise ValueError("Every argument must be a string")

    if "env" not in config:
        raise ValueError("env must be provided")

    env = config["env"]
    if not isinstance(env, dict):
        raise ValueError("env must be a dictionary")

    if not all(isinstance(key, str) and key.strip() for key in env):
        raise ValueError("Environment variable names must be non-empty strings")

    if not all(isinstance(value, str) for value in env.values()):
        raise ValueError("Environment variable values must be strings")

    return {
        "valid": True,
        "command": command,
        "args": args.copy(),
        "environment_keys": sorted(env.keys()),
        "environment_values_redacted": True,
        "process_launched": False,
    }


def run_experiment():
    """Compare three controlled local configuration sizes."""

    fixtures = [
        {
            "name": "Small",
            "config": {
                "command": "python3",
                "args": ["server.py"],
                "env": {"MODE": "demo"},
            },
        },
        {
            "name": "Medium",
            "config": {
                "command": "python3",
                "args": ["server.py", "--port", "8000"],
                "env": {"MODE": "demo", "API_KEY": "mock-secret"},
            },
        },
        {
            "name": "Large",
            "config": {
                "command": "python3",
                "args": [
                    "server.py", "--port", "8000",
                    "--host", "localhost",
                ],
                "env": {
                    "MODE": "demo",
                    "API_KEY": "mock-secret",
                    "LOG_LEVEL": "INFO",
                    "REGION": "local",
                },
            },
        },
    ]

    results = []

    for fixture in fixtures:
        config = fixture["config"]

        try:
            summary = validate_config(config)
            actual = "PASS"
        except ValueError:
            summary = None
            actual = "FAIL"

        expected = "PASS"

        results.append({
            "configuration": fixture["name"],
            "argument_count": len(config["args"]),
            "environment_key_count": len(config["env"]),
            "expected": expected,
            "actual": actual,
            "correct": expected == actual,
            "summary": summary,
        })

    return results


if __name__ == "__main__":
    import json

    print("MCP Configuration Validation Experiment")
    print("Simulation only - no process launched.\n")

    print(json.dumps(run_experiment(), indent=4))
