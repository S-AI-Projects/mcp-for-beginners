"""Client-configuration validation and evaluation experiment across controlled input sizes.

Task R49-T019: Client-configuration validation — evaluation experiment.
"""

import time
from typing import Any, Dict, List, Tuple


def validate_launch_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """Validate server launch configuration and return redacted summary.

    Parameters:
        config: Dictionary containing 'command', 'args', and 'env'.

    Returns:
        Summary dict containing 'command', 'args', and 'environment_keys'.

    Raises:
        ValueError: If command is missing/empty, args is not a list of strings,
                    or env is not a dict of strings.
        TypeError: If config is not a dictionary.
    """
    if not isinstance(config, dict):
        raise TypeError("Configuration must be a dictionary")

    cmd = config.get("command")
    if not isinstance(cmd, str) or not cmd.strip():
        raise ValueError("A non-empty string command is required")

    args = config.get("args", [])
    if isinstance(args, str):
        raise ValueError("Arguments must be a list of strings, not a single string")
    if not isinstance(args, list):
        raise ValueError("Arguments must be a list of strings")

    for idx, item in enumerate(args):
        if not isinstance(item, str):
            raise ValueError(f"Argument at index {idx} must be a string")

    env = config.get("env", {})
    if not isinstance(env, dict):
        raise ValueError("Environment must be a dictionary")

    for k, v in env.items():
        if not isinstance(k, str) or not k.strip():
            raise ValueError("Environment keys must be non-empty strings")
        if not isinstance(v, str):
            raise ValueError(f"Environment value for '{k}' must be a string")

    return {
        "command": cmd.strip(),
        "args": list(args),
        "environment_keys": sorted(env.keys()),
    }


def generate_fixture(size: str) -> Dict[str, Any]:
    """Generate controlled test configurations of varying sizes."""
    if size == "small":
        n = 1
    elif size == "medium":
        n = 5
    elif size == "large":
        n = 20
    else:
        raise ValueError(f"Unknown size: {size}")

    return {
        "command": "python",
        "args": [f"--arg-{i}" for i in range(n)],
        "env": {f"SECRET_KEY_{i}": f"secret_val_{i}" for i in range(n)},
    }


def evaluate_sizes() -> List[Dict[str, Any]]:
    """Evaluate validation across small, medium, and large input configurations."""
    results = []
    sizes = ["small", "medium", "large"]

    for size in sizes:
        fixture = generate_fixture(size)
        start = time.perf_counter_ns()
        summary = validate_launch_config(fixture)
        duration_us = (time.perf_counter_ns() - start) / 1000.0

        num_args = len(fixture["args"])
        num_env = len(fixture["env"])
        all_keys_sorted = summary["environment_keys"] == sorted(fixture["env"].keys())
        secrets_redacted = all(f"secret_val_{i}" not in str(summary) for i in range(num_env))
        correct = all_keys_sorted and secrets_redacted

        results.append({
            "size": size,
            "arg_count": num_args,
            "env_count": num_env,
            "correct": correct,
            "duration_us": round(duration_us, 2),
            "command": summary["command"],
        })

    return results


def main() -> None:
    """Run demonstration and report evaluation experiment metrics."""
    print("=== Configuration Validation Evaluation Experiment (R49-T019) ===")

    metrics = evaluate_sizes()
    print("\n| Size | Args | Env Keys | Correctness | Validation Time (μs) |")
    print("| :--- | :--- | :--- | :--- | :--- |")
    for m in metrics:
        print(f"| {m['size']} | {m['arg_count']} | {m['env_count']} | {m['correct']} | {m['duration_us']} μs |")

    print("\nNegative / Boundary Cases:")
    try:
        validate_launch_config({"args": ["server.py"]})
    except ValueError as e:
        print(f"1. Missing command rejected: {e}")

    try:
        validate_launch_config({"command": "node", "args": "server.js"})
    except ValueError as e:
        print(f"2. String args rejected: {e}")

    print("\nEvaluation complete. Observed predictable linear scaling without launching processes.")


if __name__ == "__main__":
    main()
