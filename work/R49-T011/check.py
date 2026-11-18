"""Run R49-T011 scenarios and automated verification in fresh Python processes."""

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LAB = ROOT / "11-MCPServerHandsOnLabs" / "07-Semantic-Search" / "applied-labs" / "r49-t011"
RESULTS = []


def run_case(name: str, code: str, expected_success: bool) -> None:
    """Execute a test scenario snippet in an isolated Python subprocess."""
    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )

    passed = (result.returncode == 0) == expected_success

    RESULTS.append({
        "case": name,
        "expected": "exit code 0" if expected_success else "nonzero exit code",
        "actual_exit_code": result.returncode,
        "actual_stdout": result.stdout.strip(),
        "actual_stderr": result.stderr.strip(),
        "passed": passed,
    })

    assert passed, f"{name} failed: exit code {result.returncode}, stderr: {result.stderr}"
    print(f"PASS: {name}")


prefix = (
    f"import sys; sys.path.insert(0, {str(LAB)!r}); "
    "from example import SemanticSearchServerSession, negotiate_capabilities, CapabilityNotNegotiatedError; "
)

# 1. Normal scenario: Negotiate {tools, resources} & {tools, prompts} -> {tools}; dispatch tool
run_case(
    "normal_capability_negotiation_and_tool_dispatch",
    prefix
    + "session = SemanticSearchServerSession(server_capabilities={'tools', 'prompts'}); "
      "negotiated = session.negotiate({'tools', 'resources'}); "
      "assert negotiated == {'tools'}, f'Expected {{\"tools\"}}, got {negotiated}'; "
      "res = session.dispatch('tools', 'semantic_search_products', query='running shoes'); "
      "assert res['status'] == 'success' and len(res['matches']) > 0; "
      "print(res)",
    True,
)

# 2. Boundary scenario: Empty client capabilities results in empty negotiated set
run_case(
    "boundary_empty_client_capabilities",
    prefix
    + "session = SemanticSearchServerSession(server_capabilities={'tools', 'prompts'}); "
      "negotiated = session.negotiate(set()); "
      "assert negotiated == set(), f'Expected empty set, got {negotiated}'; "
      "print('Empty set negotiated successfully')",
    True,
)

# 3. Failure scenario: Calling unnegotiated capability 'resources' is rejected before dispatch
run_case(
    "failure_unnegotiated_capability_rejected_before_dispatch",
    prefix
    + "session = SemanticSearchServerSession(server_capabilities={'tools', 'prompts'}); "
      "session.negotiate({'tools', 'resources'}); "
      "session.dispatch('resources', 'read_resource', uri='resource://schema')",
    False,
)

# 4. Failure scenario: Calling dispatch before capability negotiation is performed
run_case(
    "failure_dispatch_before_negotiation",
    prefix
    + "session = SemanticSearchServerSession(server_capabilities={'tools', 'prompts'}); "
      "session.dispatch('tools', 'semantic_search_products', query='test')",
    False,
)

# 5. Unit test suite discovery
run_case(
    "unit_test_suite",
    "import sys, subprocess; "
    "r = subprocess.run([sys.executable, '-m', 'unittest', 'discover', "
    "'-s', '11-MCPServerHandsOnLabs/07-Semantic-Search/applied-labs/r49-t011', "
    "'-p', 'test_*.py'], capture_output=True, text=True); "
    "print(r.stdout); print(r.stderr); "
    "assert r.returncode == 0, 'Unit tests failed'",
    True,
)

# 6. Deliberate failure probe: verify that a failing assertion returns a nonzero exit code
probe = subprocess.run(
    [sys.executable, "-c", "assert 1 == 2"],
    capture_output=True,
    text=True,
)
assert probe.returncode != 0, "Deliberate failure probe unexpectedly succeeded"
RESULTS.append({
    "case": "deliberate_failure_probe",
    "expected": "nonzero exit code",
    "actual_exit_code": probe.returncode,
    "passed": True,
})
print("PASS: deliberate failure probe correctly returned nonzero exit code")

# Write results.json
output_file = Path(__file__).with_name("results.json")
output_file.write_text(json.dumps(RESULTS, indent=2) + "\n")
print(f"Verification evidence saved to {output_file}")
print("All R49-T011 checks passed successfully.")
