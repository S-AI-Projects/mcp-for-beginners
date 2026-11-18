"""Validate local server-launch configuration and compare approaches.

Task R49-T013: Compare direct validator implementation against an independent reference table.
"""

from typing import Any, Dict, List, Optional, Tuple


def validate_server_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """Direct implementation: validate launch config and redact environment values.

    Parameters:
        config: Dict containing 'command', optional 'args', and optional 'env'.

    Returns:
        Redacted summary dict with 'command', 'args', and 'environment_keys'.

    Raises:
        ValueError: On missing/empty command, single-string args, or invalid types.
        TypeError: If config is not a dictionary.
    """
    if not isinstance(config, dict):
        raise TypeError("Configuration must be a dictionary")

    command = config.get("command")
    if not isinstance(command, str) or not command.strip():
        raise ValueError("A non-empty command string is required")

    args = config.get("args", [])
    if isinstance(args, str):
        raise ValueError("Argument array required; single string rejected")
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
            raise ValueError(f"Environment value for {k} must be a string")

    return {
        "command": command.strip(),
        "args": list(args),
        "environment_keys": sorted(env.keys()),
    }


def reference_validate_config(config: Any) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
    """Independent reference validator using a declarative rule check.

    Returns:
        Tuple of (is_valid, redacted_result, error_reason)
    """
    if not isinstance(config, dict):
        return (False, None, "TypeError: config not dict")

    cmd = config.get("command")
    if not isinstance(cmd, str) or not cmd.strip():
        return (False, None, "ValueError: missing/empty command")

    args = config.get("args", [])
    if isinstance(args, str) or not isinstance(args, list) or any(not isinstance(a, str) for a in args):
        return (False, None, "ValueError: args must be list of strings")

    env = config.get("env", {})
    if not isinstance(env, dict) or any(not isinstance(k, str) or not k.strip() or not isinstance(v, str) for k, v in env.items()):
        return (False, None, "ValueError: env must be dict of strings")

    return (
        True,
        {
            "command": cmd.strip(),
            "args": list(args),
            "environment_keys": sorted(env.keys()),
        },
        None,
    )


# Explicit test table for comparing both approaches
BENCHMARK_CASES = [
    {
        "id": "valid_standard",
        "input": {
            "command": "python",
            "args": ["server.py", "--debug"],
            "env": {"SECRET_KEY": "sensitive_val", "ENV": "dev"},
        },
        "should_succeed": True,
        "expected_command": "python",
        "expected_args": ["server.py", "--debug"],
        "expected_keys": ["ENV", "SECRET_KEY"],
    },
    {
        "id": "valid_minimal",
        "input": {"command": "node"},
        "should_succeed": True,
        "expected_command": "node",
        "expected_args": [],
        "expected_keys": [],
    },
    {
        "id": "invalid_missing_command",
        "input": {"args": ["index.js"]},
        "should_succeed": False,
    },
    {
        "id": "invalid_single_string_args",
        "input": {"command": "uv", "args": "run server.py"},
        "should_succeed": False,
    },
]


def compare_approaches() -> List[Dict[str, Any]]:
    """Compare direct implementation and reference validation across test table."""
    comparison_results = []
    for case in BENCHMARK_CASES:
        inp = case["input"]
        # Direct execution
        try:
            direct_res = validate_server_config(inp)
            direct_success = True
            direct_data = direct_res
        except (ValueError, TypeError):
            direct_success = False
            direct_data = None

        # Reference execution
        ref_success, ref_data, _ = reference_validate_config(inp)

        match = (direct_success == ref_success == case["should_succeed"]) and (direct_data == ref_data)
        comparison_results.append({
            "case_id": case["id"],
            "direct_success": direct_success,
            "ref_success": ref_success,
            "matched": match,
            "summary": direct_data,
        })
    return comparison_results


def main() -> None:
    """Run demonstration comparing direct and reference approaches."""
    print("=== MCP Tooling: Client-Configuration Validation (R49-T013) ===")
    results = compare_approaches()
    for r in results:
        status = "AGREED" if r["matched"] else "DISAGREED"
        print(f"Case [{r['case_id']}]: {status} (success={r['direct_success']})")
        if r["summary"]:
            print(f"   Redacted Output: {r['summary']}")

    print("\nAll cases compared with identical inputs. Secret values were completely redacted.")
    print("No child processes were launched.")


if __name__ == "__main__":
    main()
