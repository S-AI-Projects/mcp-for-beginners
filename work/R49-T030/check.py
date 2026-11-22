#!/usr/bin/env python3
"""
Verification suite for Task R49-T030.
Executes test suite, saves inputs, expected vs actual results, tool versions,
and verifies that deliberate failure exits non-zero.
"""

import json
import os
import platform
import subprocess
import sys
from pathlib import Path

# Add project root to path
REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from importlib import import_module

example_module = import_module("09-CaseStudy.applied-labs.r49-t030.example")
LocalContractDispatcher = example_module.LocalContractDispatcher
get_applied_questions = example_module.get_applied_questions
verify_question_1 = example_module.verify_question_1
verify_question_2 = example_module.verify_question_2
verify_question_3 = example_module.verify_question_3

WORK_DIR = REPO_ROOT / "work" / "R49-T030"
WORK_DIR.mkdir(parents=True, exist_ok=True)


def record_tool_versions() -> None:
    git_commit = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=str(REPO_ROOT), text=True
    ).strip()
    python_version = platform.python_version()
    os_info = f"{platform.system()} {platform.release()} ({platform.machine()})"

    content = (
        f"git_commit: {git_commit}\n"
        f"python_version: {python_version}\n"
        f"platform: {os_info}\n"
        f"test_framework: unittest (standard library)\n"
    )
    (WORK_DIR / "tool_versions.txt").write_text(content)
    print("Saved tool versions.")


def run_unit_tests() -> None:
    cmd = [
        sys.executable,
        "-m",
        "unittest",
        "discover",
        "-s",
        "09-CaseStudy/applied-labs/r49-t030",
        "-p",
        "test_*.py",
        "-v",
    ]
    print("Running unittest suite...")
    res = subprocess.run(cmd, cwd=str(REPO_ROOT), capture_output=True, text=True)
    log_output = f"STDOUT:\n{res.stdout}\nSTDERR:\n{res.stderr}\nEXIT_CODE: {res.returncode}\n"
    (WORK_DIR / "test_run.log").write_text(log_output)

    if res.returncode != 0:
        print(log_output)
        raise RuntimeError(f"Unittest suite failed with exit code {res.returncode}")
    print("Unittest suite passed successfully (9 tests).")


def run_contract_and_save_evidence() -> None:
    dispatcher = LocalContractDispatcher()
    questions = {q.question_id: q for q in get_applied_questions()}

    scenarios = [
        {
            "name": "add_normal",
            "input": {"tool": "add", "arguments": {"a": 2, "b": 3}},
            "expected": {"status": "success", "result": 5},
        },
        {
            "name": "multiply_normal",
            "input": {"tool": "multiply", "arguments": {"a": 2, "b": 3}},
            "expected": {"status": "success", "result": 6},
        },
        {
            "name": "unknown_tool",
            "input": {"tool": "power", "arguments": {"a": 2, "b": 3}},
            "expected": {
                "status": "error",
                "error": {
                    "code": "UNKNOWN_TOOL",
                    "message": "Tool 'power' is not in allowlist: ['add', 'multiply']",
                },
            },
        },
        {
            "name": "string_argument_a",
            "input": {"tool": "add", "arguments": {"a": "2", "b": 3}},
            "expected": {
                "status": "error",
                "error": {
                    "code": "INVALID_ARGUMENT",
                    "parameter": "a",
                    "message": "Argument 'a' must be a number (int or float), got str: '2'",
                },
            },
        },
        {
            "name": "boolean_boundary_rejection",
            "input": {"tool": "add", "arguments": {"a": True, "b": 3}},
            "expected": {
                "status": "error",
                "error": {
                    "code": "INVALID_ARGUMENT",
                    "parameter": "a",
                    "message": "Argument 'a' must be a number (int or float), got bool: True",
                },
            },
        },
    ]

    results_data = []
    inputs_data = []

    for sc in scenarios:
        inp = sc["input"]
        expected = sc["expected"]
        actual = dispatcher.dispatch(inp)
        inputs_data.append({"scenario": sc["name"], "payload": inp})
        match = (actual == expected)
        results_data.append({
            "scenario": sc["name"],
            "expected": expected,
            "actual": actual,
            "match": match,
        })
        assert match, f"Scenario {sc['name']} failed! Expected: {expected}, got: {actual}"

    # Verify questions
    q_verifications = [
        ("Q1_PREDICT_OUTPUT", verify_question_1(dispatcher, questions["Q1_PREDICT_OUTPUT"])),
        ("Q2_DIAGNOSE_FAILURE", verify_question_2(dispatcher, questions["Q2_DIAGNOSE_FAILURE"])),
        ("Q3_BOUNDARY_POLICY", verify_question_3(dispatcher, questions["Q3_BOUNDARY_POLICY"])),
    ]

    for q_id, passed in q_verifications:
        q_obj = questions[q_id]
        results_data.append({
            "question_id": q_id,
            "category": q_obj.category,
            "factual_answer": q_obj.factual_answer,
            "rationale": q_obj.rationale,
            "verification_passed": passed,
        })
        assert passed, f"Question verification {q_id} failed!"

    (WORK_DIR / "inputs.json").write_text(json.dumps(inputs_data, indent=2))
    (WORK_DIR / "results.json").write_text(json.dumps(results_data, indent=2))
    print("Saved inputs.json and results.json successfully.")

    # Write evidence.md
    evidence_md = (
        "# Verification Evidence for Task R49-T030\n\n"
        "## Summary\n"
        "- **Allowlist Tools**: `add`, `multiply`\n"
        "- **Validation Rules**: Numeric types strictly enforced (booleans rejected, strings rejected)\n"
        "- **Fail-Fast Isolation**: Zero downstream tool invocations when schema validation fails\n"
        "- **Applied Questions Verified**:\n"
        "  1. `Q1_PREDICT_OUTPUT`: `multiply(2.5, 4)` -> `{'status': 'success', 'result': 10.0}`\n"
        "  2. `Q2_DIAGNOSE_FAILURE`: String argument `a='2'` diagnosed as `INVALID_ARGUMENT`, handlers uninvoked\n"
        "  3. `Q3_BOUNDARY_POLICY`: Strict rejection of booleans (`add(True, 3)` rejected) to safeguard protocol schema types\n"
        "- **All Scenarios Passed**: Yes (100% agreement)\n"
    )
    (WORK_DIR / "evidence.md").write_text(evidence_md)
    print("Saved evidence.md.")


def verify_deliberate_failure() -> None:
    print("Verifying deliberate failure exits non-zero...")
    failure_code = (
        "import sys, json; "
        "from importlib import import_module; "
        "m = import_module('09-CaseStudy.applied-labs.r49-t030.example'); "
        "d = m.LocalContractDispatcher(); "
        "res = d.dispatch({'tool': 'add', 'arguments': {'a': 2, 'b': 3}}); "
        "assert res['result'] == 9999, 'Deliberate wrong result check failed!' "
    )
    res = subprocess.run([sys.executable, "-c", failure_code], cwd=str(REPO_ROOT))
    if res.returncode == 0:
        raise RuntimeError("Deliberate failure did not exit with non-zero exit code!")
    print(f"Deliberate failure exited with non-zero code ({res.returncode}) as expected.")


def main() -> None:
    record_tool_versions()
    run_unit_tests()
    run_contract_and_save_evidence()
    verify_deliberate_failure()
    print("\nALL CHECKS PASSED FOR TASK R49-T030.\n")


if __name__ == "__main__":
    main()
