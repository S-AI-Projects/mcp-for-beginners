import io
import json
import unittest

from example import process_stream


class TestMessageFraming(unittest.TestCase):

    def run_stream(self, source):
        output = io.StringIO()
        diagnostics = io.StringIO()

        process_stream(
            io.StringIO(source),
            output,
            diagnostics,
        )

        results = [
            json.loads(line)
            for line in output.getvalue().splitlines()
        ]

        return results, diagnostics.getvalue()

    def test_two_messages_preserve_request_ids(self):
        source = (
            '{"jsonrpc":"2.0","id":1,"method":"ping"}\n'
            '{"jsonrpc":"2.0","id":2,"method":"ping"}\n'
        )

        results, diagnostics = self.run_stream(source)

        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["message"]["id"], 1)
        self.assertEqual(results[1]["message"]["id"], 2)
        self.assertEqual(diagnostics, "")

    def test_malformed_json_returns_structured_error(self):
        results, diagnostics = self.run_stream(
            '{"id":1,"method":"ping"}\n'
            '{"id":2,\n'
        )

        self.assertEqual(len(results), 2)
        self.assertTrue(results[0]["ok"])
        self.assertFalse(results[1]["ok"])
        self.assertEqual(
            results[1]["error"],
            {"code": "PARSE_ERROR", "line": 2},
        )
        self.assertIn("Malformed JSON on line 2", diagnostics)

    def test_diagnostic_does_not_enter_protocol_output(self):
        results, diagnostics = self.run_stream("{broken}\n")

        self.assertEqual(len(results), 1)
        self.assertNotIn("Malformed JSON", json.dumps(results))
        self.assertIn("Malformed JSON", diagnostics)

    def test_blank_lines_are_ignored(self):
        results, diagnostics = self.run_stream(
            '\n{"id":7,"method":"ping"}\n\n'
        )

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["message"]["id"], 7)
        self.assertEqual(diagnostics, "")

    def test_non_object_json_is_rejected(self):
        results, diagnostics = self.run_stream("[]\n")

        self.assertEqual(
            results[0]["error"],
            {"code": "INVALID_MESSAGE", "line": 1},
        )
        self.assertIn("Expected a JSON object", diagnostics)

    def test_empty_input_produces_no_messages(self):
        results, diagnostics = self.run_stream("")

        self.assertEqual(results, [])
        self.assertEqual(diagnostics, "")


if __name__ == "__main__":
    unittest.main()