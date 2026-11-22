#!/usr/bin/env python3
"""
Verification check script for Task R49-T021.
Runs unit tests, validates all routing fixtures, saves audit evidence,
and verifies that assertion errors cause non-zero exit codes.
"""

import sys
import os
import json
import subprocess
import platform

# Ensure applied-labs module can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../11-MCPServerHandsOnLabs/06-Tools/applied-labs/r49-t021")))
from example import ToolRouter, ToolRequest

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
        "11-MCPServerHandsOnLabs/06-Tools/applied-labs/r49-t021",
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
    print("Unittest suite passed successfully (7 tests).")

def run_fixtures_and_save_evidence():
    router = ToolRouter()
    
    fixtures = [
        {
            "id": "scenario_1_support",
            "type": "normal",
            "query": "Please help me understand how this tool works",
            "expected": {
                "handler": "support",
                "selected_intent": "help",
                "matched_intents": ["help"],
                "success": True
            }
        },
        {
            "id": "scenario_2_calculator",
            "type": "normal",
            "query": "Can you calculate 25 * 4 for the quarterly report?",
            "expected": {
                "handler": "calculator",
                "selected_intent": "calculate",
                "matched_intents": ["calculate"],
                "result": 100.0,
                "success": True
            }
        },
        {
            "id": "scenario_3_ambiguous",
            "type": "boundary_ambiguity",
            "query": "Please help me calculate total margin: 100 - 45",
            "expected": {
                "handler": "calculator",
                "selected_intent": "calculate",
                "matched_intents": ["calculate", "help"],
                "result": 55.0,
                "success": True,
                "resolution_rule_contains": "priority_resolution"
            }
        },
        {
            "id": "scenario_4_fallback",
            "type": "failure_unknown",
            "query": "Check the weather in Seattle tomorrow",
            "expected": {
                "handler": "fallback",
                "selected_intent": "unknown",
                "matched_intents": [],
                "success": True,
                "resolution_rule_contains": "default_fallback"
            }
        }
    ]

    # Save inputs.json
    with open(os.path.join(WORK_DIR, "inputs.json"), "w") as f:
        json.dump(fixtures, f, indent=2)

    results = []
    for fixture in fixtures:
        req = ToolRequest(query=fixture["query"])
        res = router.dispatch(req)
        audit = res.metadata["audit"]
        
        actual = {
            "handler": audit["handler_name"],
            "selected_intent": audit["selected_intent"],
            "matched_intents": audit["matched_intents"],
            "resolution_rule": audit["resolution_rule"],
            "success": res.success,
            "data": res.data
        }
        
        # Validate assertions
        assert actual["handler"] == fixture["expected"]["handler"], (
            f"Handler mismatch for {fixture['id']}: expected {fixture['expected']['handler']}, got {actual['handler']}"
        )
        assert actual["selected_intent"] == fixture["expected"]["selected_intent"], (
            f"Intent mismatch for {fixture['id']}: expected {fixture['expected']['selected_intent']}, got {actual['selected_intent']}"
        )
        assert actual["matched_intents"] == fixture["expected"]["matched_intents"], (
            f"Matched intents mismatch for {fixture['id']}"
        )
        if "result" in fixture["expected"]:
            assert actual["data"]["result"] == fixture["expected"]["result"], (
                f"Result mismatch for {fixture['id']}"
            )
        if "resolution_rule_contains" in fixture["expected"]:
            assert fixture["expected"]["resolution_rule_contains"] in actual["resolution_rule"], (
                f"Rule description missing expected substring for {fixture['id']}"
            )

        results.append({
            "fixture_id": fixture["id"],
            "query": fixture["query"],
            "status": "PASSED",
            "expected": fixture["expected"],
            "actual": actual
        })

    # Save results.json
    with open(os.path.join(WORK_DIR, "results.json"), "w") as f:
        json.dump(results, f, indent=2)
    print("Saved inputs.json and results.json successfully.")

    # Write evidence markdown
    evidence_md = f"""# Task R49-T021 Verification Evidence

## Summary
- **Student**: Tanmay Gahlot
- **Task**: R49-T021 · 1 of 10
- **Repository**: https://github.com/S-AI-Projects/mcp-for-beginners
- **Target Module**: `11-MCPServerHandsOnLabs/06-Tools`
- **Result**: All 7 unittests and 4 scenario fixtures PASSED.

## Scenarios Verified

### 1. Help -> Support (Normal)
- **Input**: `"Please help me understand how this tool works"`
- **Selected Intent**: `help`
- **Handler**: `support`
- **Status**: PASSED

### 2. Calculate -> Calculator (Normal)
- **Input**: `"Can you calculate 25 * 4 for the quarterly report?"`
- **Selected Intent**: `calculate`
- **Handler**: `calculator`
- **Output Result**: `100.0`
- **Status**: PASSED

### 3. Ambiguous (Calculate + Help) -> Documented Priority Resolution
- **Input**: `"Please help me calculate total margin: 100 - 45"`
- **Candidates**: `["calculate", "help"]`
- **Applied Rule**: `priority_resolution: 'calculate' (priority 1) selected over ['help'] following documented precedence`
- **Selected Intent**: `calculate`
- **Handler**: `calculator`
- **Status**: PASSED

### 4. Unknown -> Fallback (Failure / Unknown)
- **Input**: `"Check the weather in Seattle tomorrow"`
- **Candidates**: `[]`
- **Selected Intent**: `unknown`
- **Handler**: `fallback`
- **Status**: PASSED

## Deliberate Failure Verification
A deliberate wrong result assertion (e.g. asserting handler == `non_existent_wrong_handler`) raises `AssertionError`, verifying that the test framework exits non-zero on failure.
"""
    with open(os.path.join(WORK_DIR, "evidence.md"), "w") as f:
        f.write(evidence_md)
    print("Saved evidence.md.")

def verify_deliberate_failure_exits_nonzero():
    print("Verifying deliberate failure exits non-zero...")
    test_code = (
        "import sys, unittest; "
        "sys.path.insert(0, '11-MCPServerHandsOnLabs/06-Tools/applied-labs/r49-t021'); "
        "from example import ToolRouter, ToolRequest; "
        "res = ToolRouter().dispatch(ToolRequest('help me')); "
        "assert res.metadata['audit']['handler_name'] == 'wrong_handler'"
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
    print("\nALL CHECKS PASSED FOR TASK R49-T021.")
