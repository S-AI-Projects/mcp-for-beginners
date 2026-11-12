import json
import subprocess
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[2]
lab = root / "03-GettingStarted/15-mcp-apps/applied-labs/r49-t042"

sys.path.insert(0, str(lab))
from example import dispatch, compare_results

assert all(item["passed"] for item in compare_results())
assert dispatch("unknown", {"a": 2, "b": 3})["ok"] is False
assert dispatch("add", {"a": "2", "b": 3})["ok"] is False
assert dispatch("add", {"a": 2})["ok"] is False

try:
    assert dispatch("add", {"a": 2, "b": 3})["result"] == 999
except AssertionError:
    print("Deliberately wrong expected result correctly failed.")
else:
    raise SystemExit("ERROR: Wrong expected result was not detected.")

result = subprocess.run(
    [
        sys.executable,
        "-m",
        "unittest",
        "discover",
        "-s",
        str(lab),
        "-p",
        "test_*.py",
    ],
    capture_output=True,
    text=True,
)

print(result.stdout)
print(result.stderr)

if result.returncode != 0:
    raise SystemExit("ERROR: Unit tests failed.")

print("All T042 evidence checks passed.")
