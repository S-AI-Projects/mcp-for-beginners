import json
import sys
from pathlib import Path

repo = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(
    repo / "11-MCPServerHandsOnLabs/10-Deployment/applied-labs/r49-t047"
))
from example import dispatch

root = Path(__file__).resolve().parent
calls = [
    {"tool": "add", "arguments": {"a": 2, "b": 3}},
    {"tool": "multiply", "arguments": {"a": 2, "b": 3}},
    {"tool": "unknown", "arguments": {"a": 2, "b": 3}},
    {"tool": "add", "arguments": {"a": "2", "b": 3}},
]

(root / "inputs.json").write_text(json.dumps(calls, indent=2) + "\n")

log = []
actual = [dispatch(call, log) for call in calls]
expected = [
    {"ok": True, "result": 5},
    {"ok": True, "result": 6},
    {"ok": False, "error": {"code": "UNKNOWN_TOOL", "message": "Tool is not allowed"}},
    {"ok": False, "error": {"code": "INVALID_ARGUMENTS", "message": "Arguments a and b must be numbers"}},
]

if actual != expected:
    raise SystemExit("Expected and actual results do not match")

if log != ["add", "multiply"]:
    raise SystemExit("A failed call executed a tool")

try:
    assert actual[0] == {"ok": True, "result": 999}
except AssertionError:
    print("Deliberately wrong expected result was rejected.")
else:
    raise SystemExit("Wrong expected result was accepted")

results = [
    {"expected": e, "actual": a, "passed": e == a}
    for e, a in zip(expected, actual)
]
(root / "results.json").write_text(json.dumps(results, indent=2) + "\n")

print("All 4 scenarios passed.")
print("Failed calls executed no tools.")
print("Executed tools:", log)
