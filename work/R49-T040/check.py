#!/usr/bin/env python3
"""
Verification script for R49-T040: Advanced Topics Runnable Concept Example & Architectural Mapping.
"""

import json
import os
import sys

lab_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../05-AdvancedTopics/applied-labs/r49-t040"))
sys.path.insert(0, lab_dir)

from example import (
    AdvancedTopicsToolDispatcher,
    METHOD_NOT_FOUND,
    INVALID_PARAMS,
    LESSON_CONCEPT_MAPPINGS,
)


def run_checks():
    work_dir = os.path.dirname(os.path.abspath(__file__))
    inputs_file = os.path.join(work_dir, "inputs.json")
    results_file = os.path.join(work_dir, "results.json")
    mappings_file = os.path.join(work_dir, "concept_mappings_report.json")

    with open(inputs_file, "r") as f:
        inputs_data = json.load(f)

    dispatcher = AdvancedTopicsToolDispatcher()
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

    # 2. Verify Architectural Concept Mappings
    assert len(LESSON_CONCEPT_MAPPINGS) >= 5, "Must have comprehensive concept mappings"

    # Save results
    with open(results_file, "w") as f:
        json.dump({
            "status": "PASSED",
            "contract_results": contract_results,
            "execution_counts": dispatcher.execution_counts
        }, f, indent=2)

    with open(mappings_file, "w") as f:
        json.dump({
            "status": "PASSED",
            "mappings": [
                {
                    "input_or_output": m.input_or_output,
                    "lesson_concept": m.lesson_concept,
                    "architectural_rationale": m.architectural_rationale
                }
                for m in LESSON_CONCEPT_MAPPINGS
            ]
        }, f, indent=2)

    print("All R49-T040 verification checks passed successfully!")
    print(f"Results written to: {results_file}")
    print(f"Concept mappings report written to: {mappings_file}")


if __name__ == "__main__":
    run_checks()
