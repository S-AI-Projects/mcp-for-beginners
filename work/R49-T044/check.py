import json
import sys
from pathlib import Path

repo = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(repo / "06-CommunityContributions/applied-labs/r49-t044"))
from example import dispatch_tool

cases = [
    ("add", {"a": 2, "b": 3}, {"ok": True, "result": 5}),
    ("multiply", {"a": 2, "b": 3}, {"ok": True, "result": 6}),
    ("divide", {"a": 2, "b": 3}, {"ok": False, "error": {"type": "invalid_tool_call", "message": "Unknown tool"}}),
    ("add", {"a": "2", "b": 3}, {"ok": False, "error": {"type": "invalid_tool_call", "message": "Arguments a and b must be numbers"}}),
]

root = Path(__file__).resolve().parent
(root / "inputs.json").write_text(json.dumps(
    [{"tool": t, "arguments": a} for t, a, _ in cases], indent=2
) + "\n")

results = []
for tool, arguments, expected in cases:
    actual = dispatch_tool(tool, arguments)
    results.append({
        "tool": tool,
        "expected": expected,
        "actual": actual,
        "passed": actual == expected,
    })

(root / "results.json").write_text(json.dumps(results, indent=2) + "\n")

if not all(item["passed"] for item in results):
    raise SystemExit("A scenario failed")

if dispatch_tool("add", {"a": 2, "b": 3}) == {"ok": True, "result": 999}:
    raise SystemExit("Wrong expected result was not rejected")

print("All 4 scenarios passed.")
print("Deliberately wrong expected result was rejected.")
print("Evidence files created.")
