"""Run R49-T041 scenarios in separate Python processes."""

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LAB = ROOT / "03-GettingStarted/07-aitk/applied-labs/r49-t041"
RESULTS = []

def run_case(name, code, expected_success):
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

    assert passed, f"{name} failed: {result.stderr}"
    print(f"PASS: {name}")


prefix = (
    f"import sys; sys.path.insert(0, {str(LAB)!r}); "
    "from example import validate_config; "
)

run_case(
    "normal",
    prefix
    + "r = validate_config({'command':'python','args':['server.py'],"
      "'env':{'API_KEY':'secret'}}); "
      "assert r == {'command':'python','args':['server.py'],"
      "'environment_keys':['API_KEY']}; "
      "assert 'secret' not in str(r); print(r)",
    True,
)

run_case(
    "boundary_empty_arguments",
    prefix
    + "r = validate_config({'command':'python','args':[],'env':{}}); "
      "assert r['args'] == []; print(r)",
    True,
)

run_case(
    "failure_missing_command",
    prefix
    + "validate_config({'args':['server.py'],'env':{}})",
    False,
)

run_case(
    "failure_string_arguments",
    prefix
    + "validate_config({'command':'python','args':'server.py','env':{}})",
    False,
)

run_case(
    "unit_test_suite",
    "import sys, subprocess; "
    "r = subprocess.run([sys.executable, '-m', 'unittest', 'discover', "
    "'-s', '03-GettingStarted/07-aitk/applied-labs/r49-t041', "
    "'-p', 'test_*.py'], capture_output=True, text=True); "
    "print(r.stdout); print(r.stderr); "
    "assert r.returncode == 0, 'Unit tests failed'",
    True,
)

probe = subprocess.run(
    [sys.executable, "-c", "assert 1 == 2"],
    capture_output=True,
    text=True,
)
assert probe.returncode != 0, "Failure probe unexpectedly passed"
RESULTS.append({
    "case": "deliberate_failure_probe",
    "expected": "nonzero exit code",
    "actual_exit_code": probe.returncode,
    "passed": True,
})
print("PASS: deliberate failure correctly returned nonzero")

output = Path(__file__).with_name("results.json")
output.write_text(json.dumps(RESULTS, indent=2) + "\n")
print(f"Evidence saved to {output}")
print("All R49-T041 checks passed.")
