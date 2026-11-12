import sys
from pathlib import Path

repo = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(
    repo / "11-MCPServerHandsOnLabs/11-Monitoring/applied-labs/r49-t048"
))
from example import aggregate_traces, make_fixture, run_experiment

by_id = {
    item["request_id"]: item
    for item in aggregate_traces(make_fixture(0))
}

assert by_id["A"]["duration_ms"] == 12
assert by_id["A"]["tool_calls"] == 2
assert by_id["B"]["status"] == "failure"
assert by_id["C"]["status"] == "incomplete"
assert by_id["C"]["duration_ms"] is None

experiment = run_experiment()
assert len(experiment) == 3
assert all(item["correct"] for item in experiment)

try:
    assert by_id["A"]["duration_ms"] == 999
except AssertionError:
    print("Deliberately wrong expected result was rejected.")
else:
    raise SystemExit("Wrong expected result was accepted")

print("All trace scenarios passed.")
print("Experiment:", experiment)
