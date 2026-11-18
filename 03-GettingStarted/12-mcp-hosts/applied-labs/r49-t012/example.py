"""Validate local server-launch configuration and redact secrets without launching processes.

Task R49-T012: Boundary-case lesson extension for MCP Host Clients.
"""

from typing import Any, Dict, List, Optional


def validate_launch_configuration(config: Dict[str, Any]) -> Dict[str, Any]:
    """Validate a local server-launch configuration and return a redacted summary.

    Parameters:
        config: Dictionary containing 'command', optional 'args', and optional 'env'.

    Returns:
        Redacted configuration dictionary with keys 'command', 'args', and 'environment_keys'.

    Raises:
        ValueError: If command is missing/empty, args is not a list of strings,
                    or env is not a dict of strings.
        TypeError: If config is not a dictionary.
    """
    if not isinstance(config, dict):
        raise TypeError("Configuration must be a dictionary")

    command = config.get("command")
    if not isinstance(command, str) or not command.strip():
        raise ValueError("A non-empty string 'command' is required")

    args = config.get("args", [])
    if isinstance(args, str):
        raise ValueError("Arguments must be a list of strings, not a single string")
    if not isinstance(args, list):
        raise ValueError("Arguments must be a list of strings")

    for idx, arg in enumerate(args):
        if not isinstance(arg, str):
            raise ValueError(f"Argument at index {idx} must be a string, got {type(arg).__name__}")

    env = config.get("env", {})
    if not isinstance(env, dict):
        raise ValueError("Environment must be a dictionary")

    for k, v in env.items():
        if not isinstance(k, str) or not k.strip():
            raise ValueError("Environment variable names must be non-empty strings")
        if not isinstance(v, str):
            raise ValueError(f"Environment variable value for '{k}' must be a string")

    return {
        "command": command.strip(),
        "args": list(args),
        "environment_keys": sorted(env.keys()),
    }


def main() -> None:
    """Demonstrate smallest valid, boundary, and invalid cases."""
    print("=== MCP Host Configuration Validation (R49-T012) ===")

    # 1. Normal configuration with secret
    normal_config = {
        "command": "node",
        "args": ["build/index.js", "--port", "3000"],
        "env": {"API_KEY": "super-secret-token", "PORT": "3000"},
    }
    summary = validate_launch_configuration(normal_config)
    print("Normal config validated successfully:")
    print(f"  Command: {summary['command']}")
    print(f"  Args: {summary['args']}")
    print(f"  Environment Keys: {summary['environment_keys']}")
    print("  (Secret values were redacted)\n")

    # 2. Smallest valid / boundary configuration
    boundary_config = {"command": "python", "args": [], "env": {}}
    b_summary = validate_launch_configuration(boundary_config)
    print("Boundary config (empty args & env) validated successfully:")
    print(f"  Summary: {b_summary}\n")

    # 3. Invalid: args passed as single string
    print("Testing invalid args (single string):")
    try:
        validate_launch_configuration({"command": "node", "args": "server.js"})
    except ValueError as e:
        print(f"  Caught expected error: {e}\n")

    # 4. Invalid: missing command
    print("Testing missing command:")
    try:
        validate_launch_configuration({"args": ["server.js"]})
    except ValueError as e:
        print(f"  Caught expected error: {e}\n")

    print("Demo completed successfully. No server process was launched.")


if __name__ == "__main__":
    main()
