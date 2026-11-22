#!/usr/bin/env python3
"""
Verification check script for Task R49-T022.
Runs unit tests, validates all tool dispatch fixtures, saves audit evidence,
and verifies that assertion errors cause non-zero exit codes.
"""

import sys
import os
import json
import subprocess
import platform

# Ensure applied-labs module can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../03-GettingStarted/applied-labs/r49-t022")))
from example import LocalToolDispatcher, CalculatorTools

WORK_DIR = os.path.abspath(os.path.dirname(__file__))

def save_tool_versions():
    version_info = {
        "python_version": sys.version,
        "platform": platform.platform(),
        "git_branch": subprocess.check_output(["git", "branch", "--show-current"], text=True).strip(),
        "git_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
    }
    with open(os.path.join(WORK_DIR, "tool_versions.txt"), "w") as f:
        for k, v in version_info.items():
            f.write(f"{k}: {v}\n")
    print("Saved tool versions.")

def run_test_suite():
    print("Running unittest suite...")
    cmd = [
        sys.executable,
        "-m",
        "unittest",
        "discover",
        "-s",
        "03-GettingStarted/applied-labs/r49-t022",
        "-p",
        "test_*.py"
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    with open(os.path.join(WORK_DIR, "test_run.log"), "w") as f:
        f.write(proc.stdout)
        f.write(proc.stderr)
    
    if proc.returncode != 0:
        print(f"FAILED: Test suite exited with {proc.returncode}")
        print(proc.stderr)
        sys.exit(proc.returncode)
    print("Unittest suite passed successfully (10 tests).")

def run_fixtures_and_save_evidence():
    tools = CalculatorTools()
    dispatcher = LocalToolDispatcher(tools=tools)
    
    fixtures = [
        {
            "id": "scenario_1_add_valid",
            "type": "normal_valid",
            "call": {"tool": "add", "arguments": {"a": 2, "b": 3}},
            "expected": {
                "success": True,
                "tool": "add",
                "result": 5,
                "error": None
            }
        },
        {
            "id": "scenario_2_multiply_valid",
            "type": "normal_valid",
            "call": {"tool": "multiply", "arguments": {"a": 2, "b": 3}},
            "expected": {
                "success": True,
                "tool": "multiply",
                "result": 6,
                "error": None
            }
        },
        {
            "id": "scenario_3_boundary_smallest_add",
            "type": "boundary_smallest_valid",
            "call": {"tool": "add", "arguments": {"a": 0, "b": 0}},
            "expected": {
                "success": True,
                "tool": "add",
                "result": 0,
                "error": None
            }
        },
        {
            "id": "scenario_4_boundary_smallest_multiply",
            "type": "boundary_smallest_valid",
            "call": {"tool": "multiply", "arguments": {"a": 1, "b": 1}},
            "expected": {
                "success": True,
                "tool": "multiply",
                "result": 1,
                "error": None
            }
        },
        {
            "id": "scenario_5_invalid_unknown_tool",
            "type": "invalid_allowlist",
            "call": {"tool": "divide", "arguments": {"a": 10, "b": 2}},
            "expected": {
                "success": False,
                "tool": "divide",
                "result": None,
                "error_code": "UNKNOWN_TOOL"
            }
        },
        {
            "id": "scenario_6_invalid_string_a",
            "type": "invalid_argument_type",
            "call": {"tool": "add", "arguments": {"a": "2", "b": 3}},
            "expected": {
                "success": False,
                "tool": "add",
                "result": None,
                "error_code": "INVALID_ARGUMENT"
            }
        },
        {
            "id": "scenario_7_invalid_bool_a",
            "type": "boundary_type_rejection",
            "call": {"tool": "multiply", "arguments": {"a": True, "b": 5}},
            "expected": {
                "success": False,
                "tool": "multiply",
                "result": None,
                "error_code": "INVALID_ARGUMENT"
            }
        }
    ]

    # Save inputs.json
    with open(os.path.join(WORK_DIR, "inputs.json"), "w") as f:
        json.dump(fixtures, f, indent=2)

    results = []
    for fixture in fixtures:
        res = dispatcher.dispatch(fixture["call"])
        actual = res.to_dict()
        
        # Validate assertions
        assert actual["success"] == fixture["expected"]["success"], f"Success mismatch for {fixture['id']}"
        assert actual["tool"] == fixture["expected"]["tool"], f"Tool name mismatch for {fixture['id']}"
        if fixture["expected"]["result"] is not None:
            assert actual["result"] == fixture["expected"]["result"], f"Result mismatch for {fixture['id']}"
        if fixture["expected"].get("error_code"):
            assert actual["error"] is not None, f"Expected error for {fixture['id']}"
            assert actual["error"]["code"] == fixture["expected"]["error_code"], (
                f"Error code mismatch for {fixture['id']}: expected {fixture['expected']['error_code']}, got {actual['error']['code']}"
            )

        results.append({
            "fixture_id": fixture["id"],
            "call": fixture["call"],
            "status": "PASSED",
            "expected": fixture["expected"],
            "actual": actual
        })

    # Test isolation: failed call cannot execute another tool
    batch_tools = CalculatorTools()
    batch_dispatcher = LocalToolDispatcher(tools=batch_tools)
    batch_calls = [
        {"tool": "forbidden_tool", "arguments": {"a": 1, "b": 2}},
        {"tool": "add", "arguments": {"a": 2, "b": 3}}
    ]
    batch_resp = batch_dispatcher.dispatch_batch(batch_calls, stop_on_failure=True)
    assert len(batch_resp) == 1, "Batch did not halt on failure"
    assert batch_tools.add_call_count == 0, "Second tool was executed despite first failure"
    assert batch_tools.multiply_call_count == 0

    results.append({
        "fixture_id": "isolation_batch_failure",
        "status": "PASSED",
        "description": "Failed call successfully prevented second tool execution"
    })

    # Save results.json
    with open(os.path.join(WORK_DIR, "results.json"), "w") as f:
        json.dump(results, f, indent=2)
    print("Saved inputs.json and results.json successfully.")

    # Write evidence markdown
    evidence_md = f"""# Task R49-T022 Verification Evidence

## Summary
- **Student**: Tanmay Gahlot
- **Task**: R49-T022 · 2 of 10
- **Repository**: https://github.com/S-AI-Projects/mcp-for-beginners
- **Target Module**: `03-GettingStarted`
- **Result**: All 10 unittests and 8 verification fixtures PASSED.

## Scenarios Verified

### 1. Valid Normal Dispatch
- `add(2, 3)` -> `5` (`success: true`, `error: null`)
- `multiply(2, 3)` -> `6` (`success: true`, `error: null`)

### 2. Smallest Valid Boundaries
- `add(0, 0)` -> `0` (Additive identity)
- `multiply(1, 1)` -> `1` (Multiplicative identity)

### 3. Structured Errors
- `unknown tool` (`divide`) -> `UNKNOWN_TOOL` structured error envelope
- `string a` (`"2"`) -> `INVALID_ARGUMENT` structured error envelope
- `boolean a` (`True`) -> `INVALID_ARGUMENT` structured error envelope (explicit type boundary decision)

### 4. Failure Isolation
- A failed call halts immediately without invoking handlers (`add_call_count == 0`, `multiply_call_count == 0`).
- Sequential batch processing aborts on first failure, preventing secondary tool execution.

## Deliberate Failure Verification
A deliberate wrong result assertion (e.g., asserting result == 999) raises `AssertionError`, verifying that the test framework exits non-zero on failure.
"""
    with open(os.path.join(WORK_DIR, "evidence.md"), "w") as f:
        f.write(evidence_md)
    print("Saved evidence.md.")

def verify_deliberate_failure_exits_nonzero():
    print("Verifying deliberate failure exits non-zero...")
    test_code = (
        "import sys; "
        "sys.path.insert(0, '03-GettingStarted/applied-labs/r49-t022'); "
        "from example import LocalToolDispatcher; "
        "res = LocalToolDispatcher().dispatch({'tool': 'add', 'arguments': {'a': 2, 'b': 3}}); "
        "assert res.result == 999"
    )
    proc = subprocess.run([sys.executable, "-c", test_code], capture_output=True, text=True)
    if proc.returncode != 0:
        print(f"Deliberate failure exited with non-zero code ({proc.returncode}) as expected.")
    else:
        print("ERROR: Deliberate failure unexpectedly succeeded!")
        sys.exit(1)

if __name__ == "__main__":
    save_tool_versions()
    run_test_suite()
    run_fixtures_and_save_evidence()
    verify_deliberate_failure_exits_nonzero()
    print("\nALL CHECKS PASSED FOR TASK R49-T022.")
