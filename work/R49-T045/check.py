import json
import sys
from pathlib import Path

repo = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(repo / "02-Security/applied-labs/r49-t045"))
from example import authenticate

cases = [
    (None, {"status": "unauthenticated", "subject": None}),
    ("wrong-token", {"status": "invalid", "subject": None}),
    ("demo-valid-token", {"status": "authenticated", "subject": "student-001"}),
]

root = Path(__file__).resolve().parent
(root / "inputs.json").write_text(json.dumps(
    [{"token_present": token is not None} for token, _ in cases], indent=2
) + "\n")

results = []
for token, expected in cases:
    actual = authenticate(token)
    results.append({
        "input": "missing" if token is None else "provided",
        "expected": expected,
        "actual": actual,
        "passed": actual == expected,
    })

(root / "results.json").write_text(json.dumps(results, indent=2) + "\n")

if not all(item["passed"] for item in results):
    raise SystemExit("A scenario failed")

if authenticate("demo-valid-token") == {
    "status": "authenticated", "subject": "wrong-subject"
}:
    raise SystemExit("Wrong expected result was accepted")

print("All 3 authentication scenarios passed.")
print("Deliberately wrong expected result was rejected.")
