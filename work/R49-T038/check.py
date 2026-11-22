#!/usr/bin/env python3
"""
Verification script for R49-T038: Typed Tool Dispatch, Failure & Recovery.
"""

import json
import os
import sys

lab_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../11-MCPServerHandsOnLabs/applied-labs/r49-t038"))
sys.path.insert(0, lab_dir)

from example import (
    FailureRecoveryToolDispatcher,
    METHOD_NOT_FOUND,
    INVALID_PARAMS,
    exercise_failure_and_recovery,
)


def run_checks():
    work_dir = os.path.dirname(os.path.abspath(__file__))
    inputs_file = os.path.join(work_dir, "inputs.json")
    results_file = os.path.join(work_dir, "results.json")
    recovery_report_file = os.path.join(work_dir, "recovery_report.json")

    with open(inputs_file, "r") as f:
        inputs_data = json.load(f)

    dispatcher = FailureRecoveryToolDispatcher()
    contract_results = []

    # 1. Verify Contract Cases
    for tc in inputs_data["contract_test_cases"]:
        req = {
            "jsonrpc": "2.0",
            "id": tc["id"],
            "tool": tc["tool"],
            "params": tc["params"]
        }
        res = dispatcher.dispatch(req)
        contract_results.append({
            "id": tc["id"],
            "tool": tc["tool"],
            "request": req,
            "response": res
        })

    # Assert contract outputs
    assert contract_results[0]["response"].get("result", {}).get("value") == 5, "add(2,3) must equal 5"
    assert contract_results[1]["response"].get("result", {}).get("value") == 6, "multiply(2,3) must equal 6"
    assert contract_results[2]["response"].get("error", {}).get("code") == METHOD_NOT_FOUND, "Unknown tool must return -32601"
    assert contract_results[3]["response"].get("error", {}).get("code") == INVALID_PARAMS, "String parameter must return -32602"

    # Circuit isolation assertion
    assert dispatcher.get_tool_call_count("add") == 1
    assert dispatcher.get_tool_call_count("multiply") == 1

    # 2. Verify Failure & Recovery Flow
    steps = exercise_failure_and_recovery()
    assert len(steps) == 4, "Expected 4 recovery steps"
    assert steps[0].is_success, "Step 1 should be success"
    assert not steps[1].is_success, "Step 2 should be failure (missing param)"
    assert steps[1].response.get("error", {}).get("code") == INVALID_PARAMS
    assert not steps[2].is_success, "Step 3 should be failure (string param)"
    assert steps[2].response.get("error", {}).get("code") == INVALID_PARAMS
    assert steps[3].is_success, "Step 4 should be recovery success"
    assert steps[3].response.get("result", {}).get("value") == 6

    # Save results
    with open(results_file, "w") as f:
        json.dump({
            "status": "PASSED",
            "contract_results": contract_results,
            "execution_counts": dispatcher.execution_counts
        }, f, indent=2)

    with open(recovery_report_file, "w") as f:
        json.dump({
            "status": "PASSED",
            "steps": [
                {
                    "step_id": s.step_id,
                    "step_name": s.step_name,
                    "request": s.request,
                    "response": s.response,
                    "is_success": s.is_success,
                    "explanation": s.explanation
                }
                for s in steps
            ]
        }, f, indent=2)

    print("All R49-T038 verification checks passed successfully!")
    print(f"Results written to: {results_file}")
    print(f"Recovery report written to: {recovery_report_file}")


if __name__ == "__main__":
    run_checks()
