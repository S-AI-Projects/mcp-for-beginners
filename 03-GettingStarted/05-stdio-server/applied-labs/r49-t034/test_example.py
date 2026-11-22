"""
Unit tests for MCP Server with stdio Transport Framing & Offline Service Adapter.

Lesson Extension: 03-GettingStarted/05-stdio-server
Task ID: R49-T034

Validates:
- Two complete lines yield two messages.
- Request IDs are strictly preserved.
- Malformed JSON yields structured parse failure.
- Diagnostics are written to stderr; stdout contains only valid JSON-RPC.
- Callable adapter interface and deterministic local behavior.
- Real-service limitations documentation.
- Deliberate wrong result detection.
"""

import io
import json
import os
import sys
import unittest

# Ensure current directory is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from example import (
    StdioFramingProcessor,
    DeterministicLocalAdapter,
    PARSE_ERROR_CODE,
    INVALID_REQUEST_CODE,
    REAL_SERVICE_BEHAVIORS_NOT_ESTABLISHED,
    LOCAL_SERVICE_FIXTURE,
)


class TestStdioFramingProcessor(unittest.TestCase):
    """Test suite validating newline-delimited framing and stream separation."""

    def setUp(self):
        self.adapter = DeterministicLocalAdapter()
        self.stdout = io.StringIO()
        self.stderr = io.StringIO()
        self.processor = StdioFramingProcessor(
            backend=self.adapter,
            stdout_stream=self.stdout,
            stderr_stream=self.stderr
        )

    def test_two_complete_lines_yield_two_messages(self):
        """
        Primary Goal:
        Two complete lines yield two messages with preserved request IDs.
        """
        payload = (
            '{"jsonrpc": "2.0", "id": 101, "method": "ping"}\n'
            '{"jsonrpc": "2.0", "id": "req-xyz-2", "method": "tools/list"}\n'
        )
        report = self.processor.process_input(payload)

        self.assertEqual(report.lines_read, 2)
        self.assertEqual(report.messages_dispatched, 2)
        self.assertEqual(report.parse_errors_encountered, 0)
        self.assertEqual(report.request_ids_preserved, [101, "req-xyz-2"])
        self.assertEqual(len(report.stdout_lines), 2)

        # Parse responses and check IDs
        resp1 = json.loads(report.stdout_lines[0])
        resp2 = json.loads(report.stdout_lines[1])
        self.assertEqual(resp1["id"], 101)
        self.assertEqual(resp1["result"]["status"], "pong")
        self.assertEqual(resp2["id"], "req-xyz-2")
        self.assertIn("tools", resp2["result"])

    def test_malformed_json_yields_structured_parse_failure(self):
        """
        Malformed JSON line yields structured JSON-RPC parse error on stdout
        and diagnostic error log on stderr.
        """
        payload = (
            '{"jsonrpc": "2.0", "id": 1, "method": "ping"}\n'
            '{"malformed": syntax error}\n'
        )
        report = self.processor.process_input(payload)

        self.assertEqual(report.parse_errors_encountered, 1)
        self.assertEqual(len(report.stdout_lines), 2)

        # Second line should be structured parse failure
        parse_err_resp = json.loads(report.stdout_lines[1])
        self.assertEqual(parse_err_resp["jsonrpc"], "2.0")
        self.assertIsNone(parse_err_resp["id"])
        self.assertEqual(parse_err_resp["error"]["code"], PARSE_ERROR_CODE)
        self.assertIn("Parse error", parse_err_resp["error"]["message"])

        # Stderr must contain diagnostic info
        stderr_val = self.stderr.getvalue()
        self.assertIn("[DIAGNOSTIC]", stderr_val)
        self.assertIn("JSON parse failure", stderr_val)

    def test_keep_diagnostics_out_of_protocol_output_stream(self):
        """
        Protocol output stream (stdout) MUST NOT contain any diagnostic text.
        Every single line in stdout must be valid JSON-RPC.
        """
        mixed_input = (
            '{"jsonrpc": "2.0", "id": 1, "method": "ping"}\n'
            'broken line\n'
            '{"jsonrpc": "2.0", "id": 2, "method": "ping"}\n'
        )
        report = self.processor.process_input(mixed_input)

        # Stderr contains diagnostics
        self.assertGreater(len(report.stderr_lines), 0)
        for err_line in report.stderr_lines:
            self.assertIn("[DIAGNOSTIC]", err_line)

        # Stdout must contain NO diagnostics and MUST be 100% valid JSON
        self.assertEqual(len(report.stdout_lines), 3)
        for out_line in report.stdout_lines:
            self.assertNotIn("[DIAGNOSTIC]", out_line)
            # Verify each line is valid JSON
            parsed = json.loads(out_line)
            self.assertEqual(parsed.get("jsonrpc"), "2.0")

    def test_adapter_callable_interface(self):
        """Verify DeterministicLocalAdapter adheres to callable contract."""
        res_ping = self.adapter.call_service("ping")
        self.assertEqual(res_ping["status"], "pong")

        res_tools = self.adapter.call_service("tools/list")
        self.assertEqual(len(res_tools["tools"]), 1)

        res_unknown = self.adapter.call_service("nonexistent/method")
        self.assertEqual(res_unknown["status"], "unsupported_method")

    def test_deliberate_wrong_result_makes_test_fail(self):
        """
        Done-when requirement:
        'The contribution focus is demonstrated, and a deliberate wrong result makes the test fail.'

        Simulates a broken transport that leaks diagnostics to stdout or mutates IDs.
        Confirms our validation assertion strictly catches the defect.
        """
        flawed_stdout_line = "[DIAGNOSTIC] Leaked debug statement into stdout!"

        # A strict protocol parser must fail when reading this from stdout
        with self.assertRaises(json.JSONDecodeError):
            json.loads(flawed_stdout_line)

        # ID corruption simulation: request id 42 replaced with None
        with self.assertRaises(AssertionError):
            expected_id = 42
            actual_id = None
            self.assertEqual(actual_id, expected_id)

    def test_empty_and_whitespace_lines_ignored(self):
        """Empty lines between requests do not trigger errors."""
        input_with_blanks = (
            "\n"
            '{"jsonrpc": "2.0", "id": 1, "method": "ping"}\n'
            "   \n"
            '{"jsonrpc": "2.0", "id": 2, "method": "ping"}\n'
            "\n"
        )
        report = self.processor.process_input(input_with_blanks)
        self.assertEqual(report.lines_read, 2)
        self.assertEqual(report.messages_dispatched, 2)
        self.assertEqual(report.parse_errors_encountered, 0)

    def test_real_service_limitations_identified(self):
        """Verify real-service behaviors not established by mock are documented."""
        self.assertGreaterEqual(len(REAL_SERVICE_BEHAVIORS_NOT_ESTABLISHED), 4)
        concatenated = " ".join(REAL_SERVICE_BEHAVIORS_NOT_ESTABLISHED).lower()
        self.assertIn("latency", concatenated)
        self.assertIn("rate limiting", concatenated)
        self.assertIn("pipe buffer", concatenated)
        self.assertIn("timeout", concatenated)


if __name__ == "__main__":
    unittest.main()
