import unittest
from example import aggregate_traces, make_fixture, run_experiment


class TraceAggregationTests(unittest.TestCase):
    def test_request_a_has_two_calls_and_12ms_duration(self):
        result = aggregate_traces(make_fixture(0))
        request_a = next(item for item in result if item["request_id"] == "A")
        self.assertEqual(request_a, {
            "request_id": "A",
            "duration_ms": 12,
            "tool_calls": 2,
            "status": "success",
        })

    def test_request_b_is_failure(self):
        result = aggregate_traces(make_fixture(0))
        request_b = next(item for item in result if item["request_id"] == "B")
        self.assertEqual(request_b["status"], "failure")

    def test_missing_end_is_incomplete_not_zero(self):
        result = aggregate_traces(make_fixture(0))
        request_c = next(item for item in result if item["request_id"] == "C")
        self.assertEqual(request_c["status"], "incomplete")
        self.assertIsNone(request_c["duration_ms"])

    def test_prompt_content_is_not_in_summary(self):
        events = [
            {"request_id": "X", "type": "request_start",
             "timestamp_ms": 1, "prompt": "private prompt"},
            {"request_id": "X", "type": "request_end",
             "timestamp_ms": 3, "success": True},
        ]
        summary = aggregate_traces(events)
        self.assertNotIn("prompt", str(summary))
        self.assertNotIn("private prompt", str(summary))

    def test_three_input_sizes_are_correct(self):
        results = run_experiment()
        self.assertEqual(len(results), 3)
        self.assertTrue(all(item["correct"] for item in results))
        self.assertEqual(
            [item["extra_requests"] for item in results],
            [0, 100, 1000],
        )

    def test_empty_input(self):
        self.assertEqual(aggregate_traces([]), [])


if __name__ == "__main__":
    unittest.main()
