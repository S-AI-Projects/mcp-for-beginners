#!/usr/bin/env python3
"""
Automated Verification and Evidence Collector for R49-T036.

Task: R49-T036 (Issue #36 / Task 6)
Item: 11-MCPServerHandsOnLabs/11-Monitoring
Focus: Trace aggregation, duration/tool metrics, prompt omission, and before/after equivalence.

This script:
1. Records tool versions in work/R49-T036/tool_versions.txt.
2. Captures exact inputs and expected vs actual results in inputs.json & results.json.
3. Records before/after refactoring equivalence evidence in equivalence_report.json.
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
    "11-Monitoring",
    "applied-labs",
    "r49-t036"
)

if LAB_DIR not in sys.path:
    sys.path.insert(0, LAB_DIR)

from example import (
    BaselineTraceAggregator,
    RefactoredTraceAggregator,
    verify_before_after_equivalence,
    LOCAL_TRACE_FIXTURE,
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
    baseline = BaselineTraceAggregator()
    refactored = RefactoredTraceAggregator()

    inputs_record = {"raw_trace_events": LOCAL_TRACE_FIXTURE}
    results_record = {}

    # Run refactored aggregator
    summary = refactored.aggregate(LOCAL_TRACE_FIXTURE)

    # 1. Assert Request A
    req_a = summary.get("req-A")
    assert req_a is not None, "Missing req-A in summary!"
    assert req_a["status"] == "SUCCESS", f"req-A status wrong: {req_a['status']}"
    assert req_a["duration_ms"] == 12, f"req-A duration wrong: {req_a['duration_ms']}"
    assert req_a["tool_call_count"] == 2, f"req-A tool count wrong: {req_a['tool_call_count']}"

    # 2. Assert Request B
    req_b = summary.get("req-B")
    assert req_b is not None, "Missing req-B in summary!"
    assert req_b["status"] == "FAILURE", f"req-B status wrong: {req_b['status']}"
    assert req_b["error"] == "Database connection timeout", f"req-B error wrong: {req_b['error']}"

    # 3. Assert Request C (Missing end event)
    req_c = summary.get("req-C")
    assert req_c is not None, "Missing req-C in summary!"
    assert req_c["status"] == "INCOMPLETE", f"req-C status wrong: {req_c['status']}"
    assert req_c["duration_ms"] is None, f"req-C duration should be None, got: {req_c['duration_ms']}"

    # 4. Assert Prompt Redaction
    dumped = json.dumps(summary)
    assert '"prompt"' not in dumped, "Key 'prompt' found in summary output!"
    for ev in LOCAL_TRACE_FIXTURE:
        prompt_val = ev.get("prompt")
        if prompt_val:
            assert prompt_val not in dumped, f"Raw prompt '{prompt_val}' leaked into summary!"

    # 5. Assert Before/After Equivalence
    is_equiv, base_out, ref_out = verify_before_after_equivalence(LOCAL_TRACE_FIXTURE)
    assert is_equiv, "Baseline and Refactored outputs diverged!"
    assert base_out == ref_out

    results_record = {
        "req_A": req_a,
        "req_B": req_b,
        "req_C": req_c,
        "prompts_omitted": True,
        "missing_end_marked_incomplete": True,
        "before_after_equivalent": True,
    }

    equivalence_report = {
        "baseline_output": base_out,
        "refactored_output": ref_out,
        "is_identical": is_equiv,
        "extracted_responsibility": "TraceLifecycleClassifier",
    }

    # Save artifacts
    with open(os.path.join(SCRIPT_DIR, "inputs.json"), "w") as f:
        json.dump(inputs_record, f, indent=2)
    print(f"[OK] Inputs recorded to {os.path.join(SCRIPT_DIR, 'inputs.json')}")

    with open(os.path.join(SCRIPT_DIR, "results.json"), "w") as f:
        json.dump(results_record, f, indent=2)
    print(f"[OK] Results recorded to {os.path.join(SCRIPT_DIR, 'results.json')}")

    with open(os.path.join(SCRIPT_DIR, "equivalence_report.json"), "w") as f:
        json.dump(equivalence_report, f, indent=2)
    print(f"[OK] Equivalence report recorded to {os.path.join(SCRIPT_DIR, 'equivalence_report.json')}")

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
