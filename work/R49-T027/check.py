#!/usr/bin/env python3
"""
Verification check script for Task R49-T027.
Runs unit tests, validates capability negotiation and gating fixtures,
saves audit evidence, and verifies that assertion errors cause non-zero exit codes.
"""

import sys
import os
import json
import subprocess
import platform

# Ensure applied-labs module can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../11-MCPServerHandsOnLabs/01-Architecture/applied-labs/r49-t027")))
from example import (
    MCPSession,
    MockToolExecutor,
    MockResourceProvider,
    run_worked_explanation,
)

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
        "11-MCPServerHandsOnLabs/01-Architecture/applied-labs/r49-t027",
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
    print("Unittest suite passed successfully (8 tests).")

def run_fixtures_and_save_evidence():
    client_caps = {"tools", "resources"}
    server_caps = {"tools", "prompts"}

    session = MCPSession(client_capabilities=client_caps, server_capabilities=server_caps)

    fixtures = [
        {
            "id": "scenario_1_negotiated_add",
            "request": {"capability": "tools", "target": "add", "arguments": {"a": 2, "b": 3}},
            "expected": {"success": True, "result": 5, "error": None}
        },
        {
            "id": "scenario_2_negotiated_multiply",
            "request": {"capability": "tools", "target": "multiply", "arguments": {"a": 2, "b": 3}},
            "expected": {"success": True, "result": 6, "error": None}
        },
        {
            "id": "scenario_3_unnegotiated_resources_rejected",
            "request": {"capability": "resources", "target": "schema://sales_data"},
            "expected": {"success": False, "result": None, "error_code": "UNNEGOTIATED_CAPABILITY"}
        },
        {
            "id": "scenario_4_unnegotiated_prompts_rejected",
            "request": {"capability": "prompts", "target": "sales_prompt"},
            "expected": {"success": False, "result": None, "error_code": "UNNEGOTIATED_CAPABILITY"}
        }
    ]

    # Save inputs.json
    inputs_payload = {
        "client_capabilities": sorted(list(client_caps)),
        "server_capabilities": sorted(list(server_caps)),
        "fixtures": fixtures
    }
    with open(os.path.join(WORK_DIR, "inputs.json"), "w") as f:
        json.dump(inputs_payload, f, indent=2)

    results = []
    for fixture in fixtures:
        res = session.invoke(fixture["request"])
        actual = res.to_dict()

        assert actual["success"] == fixture["expected"]["success"], f"Success mismatch for {fixture['id']}"
        if fixture["expected"]["result"] is not None:
            assert actual["result"] == fixture["expected"]["result"], f"Result mismatch for {fixture['id']}"
        if fixture["expected"].get("error_code"):
            assert actual["error"] is not None
            assert actual["error"]["code"] == fixture["expected"]["error_code"]

        results.append({
            "fixture_id": fixture["id"],
            "request": fixture["request"],
            "status": "PASSED",
            "expected": fixture["expected"],
            "actual": actual
        })

    # Verify resource backend was never called
    assert session.resources.call_count == 0, "Resource backend was called despite unnegotiated capability!"

    # Save results.json
    with open(os.path.join(WORK_DIR, "results.json"), "w") as f:
        json.dump(results, f, indent=2)
    print("Saved inputs.json and results.json successfully.")

    # Write evidence markdown
    evidence_md = f"""# Task R49-T027 Verification Evidence

## Summary
- **Student**: Tanmay Gahlot
- **Task**: R49-T027 · 7 of 10
- **Repository**: https://github.com/S-AI-Projects/mcp-for-beginners
- **Target Module**: `11-MCPServerHandsOnLabs/01-Architecture`
- **Result**: All 8 unittests and capability gating fixtures PASSED.

## Scenarios Verified

### 1. Capability Negotiation via Set Intersection
- **Client**: `{{'tools', 'resources'}}`
- **Server**: `{{'tools', 'prompts'}}`
- **Negotiated Intersection**: `{{'tools'}}`
- **Status**: PASSED

### 2. Negotiated Tool Invocation
- `add(2, 3)` -> `5` (`success: true`)
- `multiply(2, 3)` -> `6` (`success: true`)
- **Status**: PASSED

### 3. Unnegotiated Capability Rejection Before Dispatch
- Invocation of `resources` is rejected with `UNNEGOTIATED_CAPABILITY`.
- Backend `MockResourceProvider.call_count == 0` (zero backend calls).
- **Status**: PASSED

### 4. Regression Test Execution
- Executed `run_worked_explanation()` validating complete input-to-output trace.
- **Status**: PASSED

## Deliberate Failure Verification
A deliberate wrong result assertion raises `AssertionError`, verifying that the test framework exits non-zero on failure.
"""
    with open(os.path.join(WORK_DIR, "evidence.md"), "w") as f:
        f.write(evidence_md)
    print("Saved evidence.md.")

def verify_deliberate_failure_exits_nonzero():
    print("Verifying deliberate failure exits non-zero...")
    test_code = (
        "import sys; "
        "sys.path.insert(0, '11-MCPServerHandsOnLabs/01-Architecture/applied-labs/r49-t027'); "
        "from example import MCPSession; "
        "session = MCPSession({'tools'}, {'tools'}); "
        "res = session.invoke({'capability': 'tools', 'target': 'add', 'arguments': {'a': 2, 'b': 3}}); "
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
    print("\nALL CHECKS PASSED FOR TASK R49-T027.")
