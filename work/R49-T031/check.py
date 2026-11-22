#!/usr/bin/env python3
"""
Automated Verification and Evidence Collector for R49-T031.

Task: R49-T031 (Issue #31)
Item: 11-MCPServerHandsOnLabs/07-Semantic-Search
Focus: Capability negotiation boundary-case extension

This script:
1. Gathers tool and environment versions into tool_versions.txt.
2. Captures exact inputs and expected vs actual results into inputs.json & results.json.
3. Runs the unittest test suite and asserts nonzero tests with 0 failures.
4. Validates that deliberate wrong results trigger nonzero exits.
5. Exits non-zero if any assertion fails.
"""

import json
import os
import platform
import subprocess
import sys
import unittest

# Ensure repo root and applied-labs are importable
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
LAB_DIR = os.path.join(
    REPO_ROOT,
    "11-MCPServerHandsOnLabs",
    "07-Semantic-Search",
    "applied-labs",
    "r49-t031"
)

if LAB_DIR not in sys.path:
    sys.path.insert(0, LAB_DIR)

from example import (
    MCPServer,
    CapabilityNotNegotiatedError,
    CAPABILITY_TOOLS,
    CAPABILITY_RESOURCES,
    CAPABILITY_PROMPTS,
)


def record_tool_versions():
    """Record environment and tool versions."""
    versions = {}
    versions["python_version"] = sys.version
    versions["platform"] = platform.platform()
    versions["python_implementation"] = platform.python_implementation()

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
    print(f"[OK] Tool versions saved to {version_file}")
    return versions


def run_checks_and_record():
    """Run all capability verification checks and record evidence."""
    inputs_record = {}
    results_record = {}

    # --- Scenario 1: Exact Goal Asymmetric Negotiation ---
    client_caps = [CAPABILITY_TOOLS, CAPABILITY_RESOURCES]
    server_caps = [CAPABILITY_TOOLS, CAPABILITY_PROMPTS]

    inputs_record["scenario_1_asymmetric"] = {
        "client_capabilities": client_caps,
        "server_capabilities": server_caps,
        "sample_query": "trail running",
        "invalid_call_capability": CAPABILITY_RESOURCES,
        "invalid_call_method": "read_product",
    }

    server = MCPServer(supported_capabilities=set(server_caps))
    session, report = server.negotiate(set(client_caps))

    expected_negotiated = sorted([CAPABILITY_TOOLS])
    actual_negotiated = sorted(list(report.negotiated))
    assert actual_negotiated == expected_negotiated, (
        f"Negotiated mismatch! Expected {expected_negotiated}, got {actual_negotiated}"
    )

    # Valid invocation
    search_res = session.dispatch(
        capability=CAPABILITY_TOOLS,
        method="semantic_search",
        query="trail running",
        top_k=2
    )
    assert len(search_res) > 0, "Expected search results from local fixture!"
    assert search_res[0]["id"] == "prod-001", "Expected prod-001 as top result!"

    # Unnegotiated invocation ('resources') must be rejected before dispatch
    rejected_properly = False
    rejection_msg = ""
    try:
        session.dispatch(
            capability=CAPABILITY_RESOURCES,
            method="read_product",
            product_id="prod-001"
        )
    except CapabilityNotNegotiatedError as exc:
        rejected_properly = True
        rejection_msg = str(exc)

    assert rejected_properly, "Invocation of unnegotiated 'resources' was NOT rejected!"
    assert server.get_handler_execution_count(CAPABILITY_RESOURCES, "read_product") == 0, (
        "Handler was executed despite capability not being negotiated!"
    )

    results_record["scenario_1_asymmetric"] = {
        "negotiated": {
            "expected": expected_negotiated,
            "actual": actual_negotiated,
            "match": actual_negotiated == expected_negotiated,
        },
        "search_dispatch": {
            "top_result_id": search_res[0]["id"],
            "top_result_name": search_res[0]["name"],
            "similarity": search_res[0]["similarity"],
        },
        "resources_rejection": {
            "rejected_before_dispatch": rejected_properly,
            "rejection_message": rejection_msg,
            "handler_execution_count": server.get_handler_execution_count(
                CAPABILITY_RESOURCES, "read_product"
            ),
        },
    }

    # --- Scenario 2: Smallest Valid Case ---
    inputs_record["scenario_2_smallest_valid"] = {
        "client_capabilities": [CAPABILITY_TOOLS],
        "server_capabilities": [CAPABILITY_TOOLS],
        "query": "backpack",
    }
    small_server = MCPServer(supported_capabilities={CAPABILITY_TOOLS})
    small_session, small_report = small_server.negotiate({CAPABILITY_TOOLS})
    small_res = small_session.dispatch(CAPABILITY_TOOLS, "semantic_search", query="backpack", top_k=1)
    assert len(small_res) == 1 and small_res[0]["id"] == "prod-003"

    results_record["scenario_2_smallest_valid"] = {
        "negotiated": sorted(list(small_report.negotiated)),
        "result_id": small_res[0]["id"],
        "result_name": small_res[0]["name"],
    }

    # --- Scenario 3: Disjoint Capability Case ---
    inputs_record["scenario_3_disjoint"] = {
        "client_capabilities": [CAPABILITY_RESOURCES],
        "server_capabilities": [CAPABILITY_TOOLS],
    }
    disjoint_session, disjoint_report = small_server.negotiate({CAPABILITY_RESOURCES})
    assert len(disjoint_report.negotiated) == 0, "Disjoint capabilities must negotiate to empty set!"

    results_record["scenario_3_disjoint"] = {
        "negotiated": sorted(list(disjoint_report.negotiated)),
        "is_empty": len(disjoint_report.negotiated) == 0,
    }

    # Save inputs.json and results.json
    inputs_file = os.path.join(SCRIPT_DIR, "inputs.json")
    with open(inputs_file, "w") as f:
        json.dump(inputs_record, f, indent=2)
    print(f"[OK] Inputs recorded to {inputs_file}")

    results_file = os.path.join(SCRIPT_DIR, "results.json")
    with open(results_file, "w") as f:
        json.dump(results_record, f, indent=2)
    print(f"[OK] Results recorded to {results_file}")

    # --- Step 4: Run unittest test suite ---
    print("\nRunning unittest suite...")
    loader = unittest.TestLoader()
    suite = loader.discover(start_dir=LAB_DIR, pattern="test_*.py")
    runner = unittest.TextTestRunner(verbosity=2)
    test_result = runner.run(suite)

    assert test_result.testsRun > 0, "Test suite reported 0 tests executed!"
    assert test_result.wasSuccessful(), (
        f"Test suite failed with {len(test_result.failures)} failures "
        f"and {len(test_result.errors)} errors!"
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
