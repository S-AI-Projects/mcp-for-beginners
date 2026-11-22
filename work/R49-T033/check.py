#!/usr/bin/env python3
"""
Automated Verification and Evidence Collector for R49-T033.

Task: R49-T033 (Issue #33 / Task 3)
Item: 03-GettingStarted/11-simple-auth
Focus: Injected verifier, intermediate state invariants, and zero token log leakage.

This script:
1. Records tool versions into work/R49-T033/tool_versions.txt.
2. Captures exact inputs and expected vs actual results into inputs.json & results.json.
3. Records detailed step-by-step intermediate traces into pipeline_traces.json.
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
    "03-GettingStarted",
    "11-simple-auth",
    "applied-labs",
    "r49-t033"
)

if LAB_DIR not in sys.path:
    sys.path.insert(0, LAB_DIR)

from example import (
    SimpleAuthPipeline,
    InjectedLocalVerifier,
    AuditLogger,
    AuthStatus,
    test_pipeline_invariants,
    LOCAL_TOKEN_FIXTURE,
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
    logger = AuditLogger()
    verifier = InjectedLocalVerifier()
    pipeline = SimpleAuthPipeline(verifier=verifier, logger=logger)

    inputs_record = {}
    results_record = {}
    traces_record = []

    test_matrix = [
        ("missing_token", {}, AuthStatus.UNAUTHENTICATED, None),
        (
            "unknown_token",
            {"Authorization": "Bearer rogue-token-secret-xyz"},
            AuthStatus.INVALID,
            None
        ),
        (
            "known_token_alice",
            {"Authorization": "Bearer bearer-alice-token-991"},
            AuthStatus.AUTHENTICATED,
            "alice_andhare"
        ),
        (
            "known_token_bob",
            {"Authorization": "Bearer bearer-bob-token-882"},
            AuthStatus.AUTHENTICATED,
            "bob_retail"
        ),
    ]

    for key, headers, exp_status, exp_subject in test_matrix:
        inputs_record[key] = {
            "has_authorization_header": "Authorization" in headers,
            "header_scheme": "Bearer" if "Authorization" in headers else None,
            "expected_status": exp_status.value,
            "expected_subject": exp_subject,
        }

        trace = pipeline.authenticate_request(headers)
        inv = test_pipeline_invariants(trace)

        # Assert contract
        assert trace.step_3_resolution.final_status == exp_status, (
            f"Expected {exp_status}, got {trace.step_3_resolution.final_status}"
        )
        assert trace.step_3_resolution.resolved_subject == exp_subject, (
            f"Expected {exp_subject}, got {trace.step_3_resolution.resolved_subject}"
        )
        assert inv["all_invariants_hold"], f"Invariant violation on {key}: {inv}"

        results_record[key] = {
            "status": trace.step_3_resolution.final_status.value,
            "resolved_subject": trace.step_3_resolution.resolved_subject,
            "error_message": trace.step_3_resolution.error_message,
            "step_1_token_extracted": trace.step_1_extraction.token_extracted,
            "step_2_verifier_invoked": trace.step_2_verification.verifier_invoked,
            "step_2_token_recognized": trace.step_2_verification.token_recognized,
            "invariants_satisfied": inv["all_invariants_hold"],
        }

        traces_record.append({
            "scenario": key,
            "trace": trace.to_dict(),
            "invariants": inv
        })

    # Log redaction verification
    for token in LOCAL_TOKEN_FIXTURE.keys():
        assert not logger.contains_raw_token(token), (
            f"CRITICAL: Raw token '{token}' found in audit logs!"
        )

    # Save artifacts
    with open(os.path.join(SCRIPT_DIR, "inputs.json"), "w") as f:
        json.dump(inputs_record, f, indent=2)
    print(f"[OK] Inputs recorded to {os.path.join(SCRIPT_DIR, 'inputs.json')}")

    with open(os.path.join(SCRIPT_DIR, "results.json"), "w") as f:
        json.dump(results_record, f, indent=2)
    print(f"[OK] Results recorded to {os.path.join(SCRIPT_DIR, 'results.json')}")

    with open(os.path.join(SCRIPT_DIR, "pipeline_traces.json"), "w") as f:
        json.dump(traces_record, f, indent=2)
    print(f"[OK] Pipeline traces recorded to {os.path.join(SCRIPT_DIR, 'pipeline_traces.json')}")

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
