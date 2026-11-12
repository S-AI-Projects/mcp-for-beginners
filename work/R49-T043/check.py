import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path("02-Security/applied-labs/r49-t043").resolve()))

from example import authenticate, fixture_verifier

cases = [
    {"case": "missing", "token": None, "expected": "unauthenticated"},
    {"case": "unknown", "token": "wrong-token", "expected": "invalid"},
    {"case": "known", "token": "fixture-token-123", "expected": "student-01"},
]

results = []

for case in cases:
    result = authenticate(case["token"], fixture_verifier)
    actual = result["status"]

    assert actual == case["expected"], case["case"]
    assert result["trace"][-1]["output"] == actual

    results.append({
        "case": case["case"],
        "expected": case["expected"],
        "actual": actual,
        "passed": True,
        "trace": result["trace"],
        "logs": result["logs"],
    })

# Confirm that a deliberately incorrect expectation is rejected.
try:
    assert authenticate(None, fixture_verifier)["status"] == "authenticated"
    raise RuntimeError("Incorrect expectation was not rejected")
except AssertionError:
    print("Deliberately wrong expected result correctly failed.")

Path("work/R49-T043/inputs.json").write_text(
    json.dumps([{"case": c["case"]} for c in cases], indent=2)
)

Path("work/R49-T043/results.json").write_text(
    json.dumps(results, indent=2)
)

print("All three authentication cases passed.")
print("Evidence files created.")
