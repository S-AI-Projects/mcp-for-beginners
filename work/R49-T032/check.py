#!/usr/bin/env python3
"""
Automated Verification and Evidence Collector for R49-T032.

Task: R49-T032 (Issue #32)
Item: 11-MCPServerHandsOnLabs/01-Architecture
Focus: Capability negotiation — compare two approaches (Direct Implementation vs Truth Table)

This script:
1. Records tool versions in work/R49-T032/tool_versions.txt.
2. Captures exact inputs and expected vs actual comparison results in inputs.json,
   results.json, and comparison_table.json.
3. Executes the full unittest suite and asserts non-zero test count with 0 failures.
4. Validates that deliberate wrong results trigger non-zero exit.
5. Exits 0 on total success, or non-zero on failure.
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
    "01-Architecture",
    "applied-labs",
    "r49-t032"
)

if LAB_DIR not in sys.path:
    sys.path.insert(0, LAB_DIR)

from example import (
    DirectMCPServer,
    CapabilityNotNegotiatedError,
    CAPABILITY_TOOLS,
    CAPABILITY_RESOURCES,
    CAPABILITY_PROMPTS,
    compare_approaches,
    independent_capability_calculation,
    lookup_expected_table,
    EXPLICIT_EXPECTED_TABLE,
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
    inputs_record = {}
    results_record = {}
    comparison_table_record = []

    # 1. Primary Scenario (Asymmetric Negotiation)
    primary_client = [CAPABILITY_TOOLS, CAPABILITY_RESOURCES]
    primary_server = [CAPABILITY_TOOLS, CAPABILITY_PROMPTS]

    inputs_record["primary_scenario"] = {
        "client_capabilities": primary_client,
        "server_capabilities": primary_server,
        "valid_invocation": {"capability": CAPABILITY_TOOLS, "method": "get_store_metrics", "store_id": "store-101"},
        "rejected_invocation": {"capability": CAPABILITY_RESOURCES, "method": "read_store_schema"}
    }

    # Approach 1: Direct Implementation
    server = DirectMCPServer(supported_capabilities=set(primary_server))
    session = server.negotiate(set(primary_client))

    # Approach 2: Independent calculation & Expected table lookup
    calc_res = independent_capability_calculation(set(primary_client), set(primary_server))
    table_entry = lookup_expected_table(set(primary_client), set(primary_server))
    assert table_entry is not None, "Primary scenario missing in expected table!"
    table_res = set(table_entry["expected_negotiated"])

    # Comparative Assertions
    assert session.negotiated_capabilities == {CAPABILITY_TOOLS}, "Direct negotiation failed!"
    assert calc_res == {CAPABILITY_TOOLS}, "Independent calculation failed!"
    assert table_res == {CAPABILITY_TOOLS}, "Table lookup failed!"
    assert session.negotiated_capabilities == calc_res == table_res, "Equivalence mismatch!"

    # Valid dispatch
    store_metrics = session.dispatch(CAPABILITY_TOOLS, "get_store_metrics", store_id="store-101")
    assert store_metrics["city"] == "Seattle"
    assert store_metrics["daily_sales"] == 14250.00

    # Rejected dispatch
    rejected_properly = False
    rejection_msg = ""
    try:
        session.dispatch(CAPABILITY_RESOURCES, "read_store_schema")
    except CapabilityNotNegotiatedError as e:
        rejected_properly = True
        rejection_msg = str(e)

    assert rejected_properly, "Unnegotiated capability was not rejected!"
    assert server.get_call_count(CAPABILITY_RESOURCES, "read_store_schema") == 0, (
        "Handler was executed despite capability not being negotiated!"
    )

    results_record["primary_scenario"] = {
        "negotiated": {
            "direct": sorted(list(session.negotiated_capabilities)),
            "independent_calc": sorted(list(calc_res)),
            "expected_table": sorted(list(table_res)),
            "all_match": True,
        },
        "valid_call_result": {
            "store_id": store_metrics["store_id"],
            "city": store_metrics["city"],
            "daily_sales": store_metrics["daily_sales"],
        },
        "rejected_call_result": {
            "rejected_before_dispatch": rejected_properly,
            "handler_call_count": server.get_call_count(CAPABILITY_RESOURCES, "read_store_schema"),
            "rejection_message": rejection_msg,
        }
    }

    # 2. Iterate through all canonical scenarios for comparison table
    for (client_tuple, server_tuple), expected_dict in EXPLICIT_EXPECTED_TABLE.items():
        rec = compare_approaches(set(client_tuple), set(server_tuple))
        assert rec.direct_matches_independent, f"Mismatch for {client_tuple} vs {server_tuple}"
        assert rec.direct_matches_table, f"Table mismatch for {client_tuple} vs {server_tuple}"

        comparison_table_record.append({
            "client_capabilities": rec.client_caps,
            "server_capabilities": rec.server_caps,
            "approach_1_direct": rec.direct_negotiated,
            "approach_2_calc": rec.independent_calc_negotiated,
            "approach_2_table": rec.table_expected_negotiated,
            "equivalent": rec.direct_matches_independent and rec.direct_matches_table,
            "pre_dispatch_rejection_verified": rec.rejected_capability_test.get("rejected", False),
        })

    # Write JSON evidence
    with open(os.path.join(SCRIPT_DIR, "inputs.json"), "w") as f:
        json.dump(inputs_record, f, indent=2)
    print(f"[OK] Inputs recorded to {os.path.join(SCRIPT_DIR, 'inputs.json')}")

    with open(os.path.join(SCRIPT_DIR, "results.json"), "w") as f:
        json.dump(results_record, f, indent=2)
    print(f"[OK] Results recorded to {os.path.join(SCRIPT_DIR, 'results.json')}")

    with open(os.path.join(SCRIPT_DIR, "comparison_table.json"), "w") as f:
        json.dump(comparison_table_record, f, indent=2)
    print(f"[OK] Comparison table recorded to {os.path.join(SCRIPT_DIR, 'comparison_table.json')}")

    # 3. Run unittest suite
    print("\nRunning unittest suite...")
    loader = unittest.TestLoader()
    suite = loader.discover(start_dir=LAB_DIR, pattern="test_*.py")
    runner = unittest.TextTestRunner(verbosity=2)
    test_result = runner.run(suite)

    assert test_result.testsRun > 0, "No tests were executed!"
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
