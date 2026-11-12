import json
import sys
from pathlib import Path

repo = Path(__file__).resolve().parents[2]
lab = repo / "12-tooling/applied-labs/r49-t046"
sys.path.insert(0, str(lab))

from example import validate_baseline, validate_configuration

fixture = {
    "command": "python",
    "args": ["server.py", "--port", "8080"],
    "env": {"API_KEY": "demo-secret", "PORT": "8080"},
}

expected = {
    "command": "python",
    "args": ["server.py", "--port", "8080"],
    "env": {"API_KEY": "[REDACTED]", "PORT": "[REDACTED]"},
}

cases = [
    ("valid configuration", fixture, expected),
]

inputs = [
    {"case": "valid configuration", "command": "python",
     "args": fixture["args"], "environment_keys": ["API_KEY", "PORT"]}
]
(repo / "work/R49-T046/inputs.json").write_text(
    json.dumps(inputs, indent=2) + "\n"
)

baseline = validate_baseline(fixture)
actual = validate_configuration(fixture)

results = [{
    "case": "baseline and refactored equivalence",
    "expected": expected,
    "baseline": baseline,
    "actual": actual,
    "passed": baseline == expected and actual == expected,
}]

for name, config, _ in cases:
    if name == "valid configuration":
        continue

if not all(item["passed"] for item in results):
    raise SystemExit("Evidence check failed")

try:
    validate_configuration(dict(fixture, command=""))
except ValueError:
    print("Boundary check passed: empty command rejected.")
else:
    raise SystemExit("Boundary check failed")

try:
    validate_configuration(dict(fixture, args="server.py"))
except ValueError:
    print("Failure check passed: string args rejected.")
else:
    raise SystemExit("Failure check failed")

wrong_expected = dict(expected, command="wrong-command")
if actual == wrong_expected:
    raise SystemExit("Deliberately wrong expected result was accepted")

results.append({
    "case": "deliberately wrong expected result",
    "expected": wrong_expected,
    "actual": actual,
    "passed": True,
    "rejected": actual != wrong_expected,
})

(repo / "work/R49-T046/results.json").write_text(
    json.dumps(results, indent=2) + "\n"
)

print("Baseline and refactored outputs match.")
print("Deliberately wrong expected result was rejected.")
print("All evidence checks passed.")
