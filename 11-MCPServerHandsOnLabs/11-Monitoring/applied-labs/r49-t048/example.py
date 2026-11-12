import json
import time


def aggregate_traces(events):
    requests = {}

    for event in events:
        request_id = event.get("request_id")
        if not request_id:
            continue

        record = requests.setdefault(request_id, {
            "request_id": request_id,
            "start_ms": None,
            "end_ms": None,
            "tool_calls": 0,
            "success": False,
            "failure": False,
        })

        event_type = event.get("type")

        if event_type == "request_start":
            record["start_ms"] = event.get("timestamp_ms")
        elif event_type == "request_end":
            record["end_ms"] = event.get("timestamp_ms")
            record["success"] = event.get("success") is True
            record["failure"] = event.get("success") is False
        elif event_type == "tool_call":
            record["tool_calls"] += 1

    summaries = []

    for request_id, record in requests.items():
        complete = (
            record["start_ms"] is not None
            and record["end_ms"] is not None
        )

        duration = (
            record["end_ms"] - record["start_ms"]
            if complete else None
        )

        summaries.append({
            "request_id": request_id,
            "duration_ms": duration,
            "tool_calls": record["tool_calls"],
            "status": (
                "incomplete" if not complete
                else "success" if record["success"]
                else "failure"
            ),
        })

    return sorted(summaries, key=lambda item: item["request_id"])


def make_fixture(size):
    events = [
        {"request_id": "A", "type": "request_start", "timestamp_ms": 100},
        {"request_id": "A", "type": "tool_call", "tool": "add"},
        {"request_id": "A", "type": "tool_call", "tool": "multiply"},
        {"request_id": "A", "type": "request_end", "timestamp_ms": 112, "success": True},
        {"request_id": "B", "type": "request_start", "timestamp_ms": 200},
        {"request_id": "B", "type": "request_end", "timestamp_ms": 205, "success": False},
        {"request_id": "C", "type": "request_start", "timestamp_ms": 300},
        {"request_id": "C", "type": "tool_call", "tool": "lookup"},
    ]

    # Add unrelated complete requests to compare three input sizes.
    for index in range(size):
        request_id = f"extra-{index:04d}"
        start = 400 + index * 10
        events.extend([
            {"request_id": request_id, "type": "request_start", "timestamp_ms": start},
            {"request_id": request_id, "type": "request_end", "timestamp_ms": start + 2, "success": True},
        ])

    return events


def run_experiment():
    results = []

    for size in (0, 100, 1000):
        events = make_fixture(size)

        start = time.perf_counter()
        summaries = aggregate_traces(events)
        elapsed_ms = (time.perf_counter() - start) * 1000

        core = {item["request_id"]: item for item in summaries}

        correct = (
            core["A"]["duration_ms"] == 12
            and core["A"]["tool_calls"] == 2
            and core["A"]["status"] == "success"
            and core["B"]["status"] == "failure"
            and core["C"]["status"] == "incomplete"
            and core["C"]["duration_ms"] is None
        )

        results.append({
            "extra_requests": size,
            "input_events": len(events),
            "correct": correct,
            "aggregation_time_ms": round(elapsed_ms, 4),
        })

    return results


if __name__ == "__main__":
    events = make_fixture(0)
    print("Trace summaries:")
    print(json.dumps(aggregate_traces(events), indent=2))
    print("\nControlled input-size experiment:")
    print(json.dumps(run_experiment(), indent=2))
    print("\nPrompt contents are not included in summaries.")
