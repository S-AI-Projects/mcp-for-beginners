#!/usr/bin/env python3
"""
Automated Verification and Evidence Collector for R49-T034.

Task: R49-T034 (Issue #34 / Task 4)
Item: 03-GettingStarted/05-stdio-server
Focus: Newline-delimited framing, request ID preservation, stdout/stderr separation,
       and offline service adapter.

This script:
1. Records tool versions into work/R49-T034/tool_versions.txt.
2. Captures exact inputs and expected vs actual results into inputs.json & results.json.
3. Records stream output verification traces in stream_traces.json.
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
    "05-stdio-server",
    "applied-labs",
    "r49-t034"
)

if LAB_DIR not in sys.path:
    sys.path.insert(0, LAB_DIR)

from example import (
    StdioFramingProcessor,
    DeterministicLocalAdapter,
    PARSE_ERROR_CODE,
    REAL_SERVICE_BEHAVIORS_NOT_ESTABLISHED,
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
    adapter = DeterministicLocalAdapter()
    processor = StdioFramingProcessor(backend=adapter)

    inputs_record = {}
    results_record = {}

    # Scenario 1: Two complete lines yield two messages
    two_lines_input = (
        '{"jsonrpc": "2.0", "id": 101, "method": "ping"}\n'
        '{"jsonrpc": "2.0", "id": "req-xyz-2", "method": "tools/list"}\n'
    )
    inputs_record["scenario_1_two_lines"] = {
        "raw_input": two_lines_input,
        "expected_messages": 2,
        "expected_ids": [101, "req-xyz-2"],
    }

    report_1 = processor.process_input(two_lines_input)
    assert report_1.messages_dispatched == 2, f"Expected 2 messages, got {report_1.messages_dispatched}"
    assert report_1.request_ids_preserved == [101, "req-xyz-2"], "Request IDs not preserved!"
    assert len(report_1.stdout_lines) == 2, "Expected 2 lines in stdout!"

    # Ensure stdout lines are strictly valid JSON-RPC
    for line in report_1.stdout_lines:
        parsed = json.loads(line)
        assert parsed.get("jsonrpc") == "2.0"
        assert "[DIAGNOSTIC]" not in line, "Leaked diagnostic into stdout!"

    # Ensure stderr has diagnostics
    assert len(report_1.stderr_lines) == 2
    for line in report_1.stderr_lines:
        assert "[DIAGNOSTIC]" in line

    results_record["scenario_1_two_lines"] = {
        "messages_dispatched": report_1.messages_dispatched,
        "request_ids_preserved": report_1.request_ids_preserved,
        "parse_errors": report_1.parse_errors_encountered,
        "stdout_valid_json": True,
        "diagnostics_in_stderr": True,
        "diagnostics_in_stdout": False,
    }

    # Scenario 2: Malformed JSON framing
    processor_2 = StdioFramingProcessor(backend=adapter)
    malformed_input = (
        '{"jsonrpc": "2.0", "id": 1, "method": "ping"}\n'
        '{"malformed_json": missing_quotes\n'
    )
    inputs_record["scenario_2_malformed_json"] = {
        "raw_input": malformed_input,
        "expected_parse_errors": 1,
    }

    report_2 = processor_2.process_input(malformed_input)
    assert report_2.parse_errors_encountered == 1, "Expected 1 parse error!"
    assert len(report_2.stdout_lines) == 2, "Expected 2 stdout lines!"

    # Line 2 must be structured error
    err_resp = json.loads(report_2.stdout_lines[1])
    assert err_resp["id"] is None
    assert err_resp["error"]["code"] == PARSE_ERROR_CODE
    assert "Parse error" in err_resp["error"]["message"]

    results_record["scenario_2_malformed_json"] = {
        "parse_errors_encountered": report_2.parse_errors_encountered,
        "error_code": err_resp["error"]["code"],
        "error_message": err_resp["error"]["message"],
        "diagnostic_written_to_stderr": any("JSON parse failure" in l for l in report_2.stderr_lines),
    }

    # Save artifacts
    with open(os.path.join(SCRIPT_DIR, "inputs.json"), "w") as f:
        json.dump(inputs_record, f, indent=2)
    print(f"[OK] Inputs recorded to {os.path.join(SCRIPT_DIR, 'inputs.json')}")

    with open(os.path.join(SCRIPT_DIR, "results.json"), "w") as f:
        json.dump(results_record, f, indent=2)
    print(f"[OK] Results recorded to {os.path.join(SCRIPT_DIR, 'results.json')}")

    stream_traces = {
        "scenario_1": {
            "stdout": report_1.stdout_lines,
            "stderr": report_1.stderr_lines,
        },
        "scenario_2": {
            "stdout": report_2.stdout_lines,
            "stderr": report_2.stderr_lines,
        },
        "real_service_limitations": REAL_SERVICE_BEHAVIORS_NOT_ESTABLISHED,
    }
    with open(os.path.join(SCRIPT_DIR, "stream_traces.json"), "w") as f:
        json.dump(stream_traces, f, indent=2)
    print(f"[OK] Stream traces recorded to {os.path.join(SCRIPT_DIR, 'stream_traces.json')}")

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
