#!/usr/bin/env python3
"""
Verification script for R49-T037: Typed Tool Dispatch and Applied Scenario Assessment.
"""

import json
import os
import sys

# Add applied-labs directory to path
lab_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../08-BestPractices/applied-labs/r49-t037"))
sys.path.insert(0, lab_dir)

from example import (
    BestPracticesToolDispatcher,
    METHOD_NOT_FOUND,
    INVALID_PARAMS,
    APPLIED_QUESTIONS,
    check_q1_predict_output,
    check_q2_diagnose_failure,
    check_q3_boundary_policy,
)


def run_checks():
    work_dir = os.path.dirname(os.path.abspath(__file__))
    inputs_file = os.path.join(work_dir, "inputs.json")
    results_file = os.path.join(work_dir, "results.json")
    questions_file = os.path.join(work_dir, "questions_report.json")

    with open(inputs_file, "r") as f:
        inputs_data = json.load(f)

    dispatcher = BestPracticesToolDispatcher()
    actual_results = []

    for tc in inputs_data["test_cases"]:
        req = {
            "jsonrpc": "2.0",
            "id": tc["id"],
            "tool": tc["tool"],
            "params": tc["params"]
        }
        res = dispatcher.dispatch(req)
        actual_results.append({
            "test_case_id": tc["id"],
            "tool": tc["tool"],
            "input": tc["params"],
            "response": res
        })

    # Assertions on contract
    # 1. add(2, 3) -> 5
    assert actual_results[0]["response"].get("result", {}).get("value") == 5, "Contract check failed for add(2,3)"
    # 2. multiply(2, 3) -> 6
    assert actual_results[1]["response"].get("result", {}).get("value") == 6, "Contract check failed for multiply(2,3)"
    # 3. unknown tool -> -32601
    assert actual_results[2]["response"].get("error", {}).get("code") == METHOD_NOT_FOUND, "Contract check failed for unknown tool"
    # 4. non-numeric string a -> -32602
    assert actual_results[3]["response"].get("error", {}).get("code") == INVALID_PARAMS, "Contract check failed for string param a"

    # Circuit isolation
    assert dispatcher.get_tool_call_count("add") == 1
    assert dispatcher.get_tool_call_count("multiply") == 1

    # Save results.json
    with open(results_file, "w") as f:
        json.dump({
            "contract": "PASSED",
            "execution_counts": dispatcher.execution_counts,
            "test_cases": actual_results
        }, f, indent=2)

    # Applied Questions Verification
    q_reports = []
    q1_passed = check_q1_predict_output()
    q2_passed = check_q2_diagnose_failure()
    q3_passed = check_q3_boundary_policy()

    assert q1_passed, "Q1 check failed"
    assert q2_passed, "Q2 check failed"
    assert q3_passed, "Q3 check failed"

    for idx, q in enumerate(APPLIED_QUESTIONS, start=1):
        q_reports.append({
            "question_number": idx,
            "category": q.category,
            "question": q.question_text,
            "factual_answer": q.factual_answer,
            "rationale": q.rationale,
            "executable_check_passed": True
        })

    with open(questions_file, "w") as f:
        json.dump({
            "questions_verified": True,
            "applied_questions": q_reports
        }, f, indent=2)

    print("All R49-T037 checks passed successfully!")
    print(f"Results written to: {results_file}")
    print(f"Questions report written to: {questions_file}")


if __name__ == "__main__":
    run_checks()
