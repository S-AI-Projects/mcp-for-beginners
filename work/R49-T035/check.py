#!/usr/bin/env python3
"""
Automated Verification and Evidence Collector for R49-T035.

Task: R49-T035 (Issue #35 / Task 5)
Item: 11-MCPServerHandsOnLabs/05-MCP-Server
Focus: Typed tool dispatch, allowlist validation, circuit isolation, and regression verification.

This script:
1. Records tool versions in work/R49-T035/tool_versions.txt.
2. Captures exact inputs and expected vs actual results in inputs.json & results.json.
3. Records worked regression test execution in regression_report.json.
4. Executes the full unittest suite and asserts non-zero tests with 0 failures.
5. Exits 0 on success, or non-zero on assertion failure.
"""

import json
import os
import platform
import subprocess
import sys
import unittest

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
LAB_DIR = os.path.join(
    REPO_ROOT,
    "11-MCPServerHandsOnLabs",
    "05-MCP-Server",
    "applied-labs",
    "r49-t035"
)

if LAB_DIR not in sys.path:
    sys.path.insert(0, LAB_DIR)

from example import (
    TypedToolDispatcher,
    METHOD_NOT_FOUND,
    INVALID_PARAMS,
    WORKED_EXAMPLES,
    TOOL_ALLOWLIST,
)


def record_tool_versions():
    versions = {
        "python_version": sys.version,
        "platform": platform.platform(),
        "python_implementation": platform.python_implementation(),
    }
    try:
        git_ver = subprocess.check_output(["git", "--version"], text=True).strip()
        versions["git_version"] = git_ver
    except Exception as e:
        versions["git_version"] = f"Unavailable: {e}"

    try:
        branch = subprocess.check_output(
            ["git", "-C", REPO_ROOT, "rev-parse", "--abbrev-ref", "HEAD"],
            text=True
        ).strip()
        versions["git_branch"] = branch
    except Exception as e:
        versions["git_branch"] = f"Unavailable: {e}"

    version_file = os.path.join(SCRIPT_DIR, "tool_versions.txt")
    with open(version_file, "w") as f:
        for k, v in versions.items():
            f.write(f"{k}: {v}\n")
    print(f"[OK] Tool versions written to {version_file}")
    return versions


def run_checks_and_record():
    dispatcher = TypedToolDispatcher()
    inputs_record = {}
    results_record = {}
    regression_report = []

    # 1. Primary Contract Checks
    # Check 1: add(2, 3) -> 5
    req_add = {"jsonrpc": "2.0", "id": 1, "tool": "add", "params": {"a": 2, "b": 3}}
    resp_add = dispatcher.dispatch(req_add)
    assert resp_add.get("result", {}).get("value") == 5, f"add(2,3) failed: {resp_add}"

    # Check 2: multiply(2, 3) -> 6
    req_mul = {"jsonrpc": "2.0", "id": 2, "tool": "multiply", "params": {"a": 2, "b": 3}}
    resp_mul = dispatcher.dispatch(req_mul)
    assert resp_mul.get("result", {}).get("value") == 6, f"multiply(2,3) failed: {resp_mul}"

    # Check 3: Unknown tool structured error
    req_unk = {"jsonrpc": "2.0", "id": 3, "tool": "divide", "params": {"a": 6, "b": 2}}
    resp_unk = dispatcher.dispatch(req_unk)
    assert resp_unk.get("error", {}).get("code") == METHOD_NOT_FOUND, f"Unknown tool failed: {resp_unk}"

    # Check 4: String 'a' structured error
    req_str = {"jsonrpc": "2.0", "id": 4, "tool": "add", "params": {"a": "2", "b": 3}}
    resp_str = dispatcher.dispatch(req_str)
    assert resp_str.get("error", {}).get("code") == INVALID_PARAMS, f"String parameter failed: {resp_str}"

    # Check 5: Failed call cannot execute another tool
    # Execution count of add should still be 1 (from first call), multiply should be 1
    assert dispatcher.get_tool_call_count("add") == 1
    assert dispatcher.get_tool_call_count("multiply") == 1

    # Record inputs and results
    inputs_record = {
        "add_call": req_add,
        "multiply_call": req_mul,
        "unknown_tool_call": req_unk,
        "string_param_call": req_str,
    }

    results_record = {
        "add_result": resp_add,
        "multiply_result": resp_mul,
        "unknown_tool_error": resp_unk,
        "string_param_error": resp_str,
        "execution_counters": dispatcher.execution_counts,
        "isolation_verified": True
    }

    # 2. Regression Test against WORKED_EXAMPLES
    reg_dispatcher = TypedToolDispatcher()
    for item in WORKED_EXAMPLES:
        out = reg_dispatcher.dispatch(item["input"])
        matched = False
        if item["expected_status"] == "SUCCESS":
            matched = (out.get("result", {}).get("value") == item["expected_value"])
        else:
            matched = (out.get("error", {}).get("code") == item["expected_error_code"])

        assert matched, f"Regression failure on {item['description']}: {out}"

        regression_report.append({
            "description": item["description"],
            "input": item["input"],
            "output": out,
            "status": "PASS" if matched else "FAIL"
        })

    # Save artifacts
    with open(os.path.join(SCRIPT_DIR, "inputs.json"), "w") as f:
        json.dump(inputs_record, f, indent=2)
    print(f"[OK] Inputs recorded to {os.path.join(SCRIPT_DIR, 'inputs.json')}")

    with open(os.path.join(SCRIPT_DIR, "results.json"), "w") as f:
        json.dump(results_record, f, indent=2)
    print(f"[OK] Results recorded to {os.path.join(SCRIPT_DIR, 'results.json')}")

    with open(os.path.join(SCRIPT_DIR, "regression_report.json"), "w") as f:
        json.dump(regression_report, f, indent=2)
    print(f"[OK] Regression report recorded to {os.path.join(SCRIPT_DIR, 'regression_report.json')}")

    # Run unittest suite
    print("\nRunning unittest suite...")
    loader = unittest.TestLoader()
    suite = loader.discover(start_dir=LAB_DIR, pattern="test_*.py")
    runner = unittest.TextTestRunner(verbosity=2)
    test_result = runner.run(suite)

    assert test_result.testsRun > 0, "No tests executed!"
    assert test_result.wasSuccessful(), (
        f"Tests failed: {len(test_result.failures)} failures, {len(test_result.errors)} errors"
    )
    print(f"[OK] Successfully executed {test_result.testsRun} unit tests with 0 failures.")


if __name__ == "__main__":
    try:
        record_tool_versions()
        run_checks_and_record()
        print("\nAll checks PASSED successfully.")
        sys.exit(0)
    except Exception as exc:
        print(f"\n[FAIL] Check assertion failed: {exc}", file=sys.stderr)
        sys.exit(1)
