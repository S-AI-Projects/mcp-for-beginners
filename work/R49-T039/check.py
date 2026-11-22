#!/usr/bin/env python3
"""
Verification script for R49-T039: Low-Level Typed Tool Dispatch & Evaluation Experiment.
"""

import json
import os
import sys

lab_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../03-GettingStarted/10-advanced/applied-labs/r49-t039"))
sys.path.insert(0, lab_dir)

from example import (
    AdvancedLowLevelDispatcher,
    METHOD_NOT_FOUND,
    INVALID_PARAMS,
    run_evaluation_experiment,
)


def run_checks():
    work_dir = os.path.dirname(os.path.abspath(__file__))
    inputs_file = os.path.join(work_dir, "inputs.json")
    results_file = os.path.join(work_dir, "results.json")
    eval_report_file = os.path.join(work_dir, "evaluation_report.json")

    with open(inputs_file, "r") as f:
        inputs_data = json.load(f)

    dispatcher = AdvancedLowLevelDispatcher()
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

    # Circuit isolation
    assert dispatcher.get_tool_call_count("add") == 1
    assert dispatcher.get_tool_call_count("multiply") == 1

    # 2. Verify Evaluation Experiment
    metrics = run_evaluation_experiment()
    assert len(metrics) == 3, "Expected 3 evaluation metrics"
    for m in metrics:
        assert m.correctness_rate == 100.0, f"Expected 100% correctness for {m.config_name}"
        assert m.unauthorized_tool_calls == 0, f"Expected 0 unauthorized calls for {m.config_name}"

    # Save results
    with open(results_file, "w") as f:
        json.dump({
            "status": "PASSED",
            "contract_results": contract_results,
            "execution_counts": dispatcher.execution_counts
        }, f, indent=2)

    with open(eval_report_file, "w") as f:
        json.dump({
            "status": "PASSED",
            "configurations_evaluated": [
                {
                    "config_name": m.config_name,
                    "input_size": m.input_size,
                    "total_calls": m.total_calls,
                    "valid_passed": m.valid_calls_passed,
                    "invalid_rejected": m.invalid_calls_rejected,
                    "unauthorized_executed": m.unauthorized_tool_calls,
                    "correctness_rate": m.correctness_rate,
                    "trade_off_summary": m.trade_off_summary
                }
                for m in metrics
            ]
        }, f, indent=2)

    print("All R49-T039 verification checks passed successfully!")
    print(f"Results written to: {results_file}")
    print(f"Evaluation report written to: {eval_report_file}")


if __name__ == "__main__":
    run_checks()
