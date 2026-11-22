"""
MCP Server with stdio Transport - Newline-Delimited Framing & Offline Service Adapter.

Lesson Extension: 03-GettingStarted/05-stdio-server
Task ID: R49-T034

Contract:
- Reads newline-delimited local JSON messages from an input stream.
- Preserves request IDs across protocol responses.
- Keeps diagnostics strictly in stderr; protocol messages strictly in stdout.
- Two complete lines yield two messages.
- Malformed JSON yields a structured parse failure on stdout and diagnostic on stderr.
- Callable interface for external service with deterministic local adapter.
- Identifies real-service behaviors that this mock does not establish.
"""

from dataclasses import dataclass, field
import io
import json
import sys
from typing import Any, Dict, List, Optional, Protocol, Tuple


# JSON-RPC Standard Error Codes
PARSE_ERROR_CODE = -32700
INVALID_REQUEST_CODE = -32600


# Deterministic Local Service Fixture
LOCAL_SERVICE_FIXTURE: Dict[str, Dict[str, Any]] = {
    "ping": {
        "status": "pong",
        "service": "local-offline-adapter",
        "version": "1.0.0"
    },
    "tools/list": {
        "tools": [
            {
                "name": "get_weather",
                "description": "Mock offline weather tool",
                "inputSchema": {"type": "object", "properties": {"city": {"type": "string"}}}
            }
        ]
    },
    "tools/call": {
        "content": [
            {"type": "text", "text": "Mock response for tool call (offline deterministic fixture)"}
        ]
    }
}


# Real-Service Behaviors NOT Established by this Local Mock
REAL_SERVICE_BEHAVIORS_NOT_ESTABLISHED: List[str] = [
    "Network latency, packet jitter, and TCP handshake/TLS negotiation overhead",
    "HTTP 429 Rate Limiting, 503 Service Unavailable, and exponential backoff retry policies",
    "Socket timeouts, dropped connections, and TCP keepalive heartbeat failures",
    "OS pipe buffer saturation (e.g. 64KB kernel buffer blocking) and SIGPIPE termination",
    "Concurrent multiplexed request-response interleaving across multiple threads/processes",
    "Payload streaming across fragmented chunked boundaries (partial line buffering across reads)"
]


class ExternalServiceBackend(Protocol):
    """Callable interface abstracting external service dependency."""
    def call_service(self, method: str, params: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        ...


class DeterministicLocalAdapter:
    """
    Deterministic offline adapter fulfilling ExternalServiceBackend protocol.
    Guarantees deterministic, local response generation without network, GPU, or paid services.
    """

    def __init__(self, fixture: Optional[Dict[str, Dict[str, Any]]] = None):
        self._fixture = fixture if fixture is not None else dict(LOCAL_SERVICE_FIXTURE)
        self.invocation_count = 0

    def call_service(self, method: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        self.invocation_count += 1
        clean_method = method.strip().lower()
        if clean_method in self._fixture:
            return self._fixture[clean_method]
        return {
            "status": "unsupported_method",
            "method": method,
            "message": f"Method '{method}' not in offline fixture."
        }


@dataclass
class FramingExecutionReport:
    """Report summarizing message framing and stream dispatch."""
    lines_read: int
    messages_dispatched: int
    parse_errors_encountered: int
    request_ids_preserved: List[Any]
    stdout_lines: List[str]
    stderr_lines: List[str]


class StdioFramingProcessor:
    """
    Processes newline-delimited JSON-RPC messages from stdin-like stream,
    writing protocol responses strictly to stdout and diagnostic logs to stderr.
    """

    def __init__(
        self,
        backend: ExternalServiceBackend,
        stdout_stream: Optional[io.StringIO] = None,
        stderr_stream: Optional[io.StringIO] = None
    ):
        self.backend = backend
        self.stdout = stdout_stream if stdout_stream is not None else io.StringIO()
        self.stderr = stderr_stream if stderr_stream is not None else io.StringIO()

    def process_input(self, raw_input: str) -> FramingExecutionReport:
        """
        Process newline-delimited stream data.
        Enforces:
        - 1 valid line -> 1 valid JSON-RPC message on stdout
        - Malformed line -> structured parse failure on stdout + diagnostic on stderr
        - Zero diagnostics on stdout
        """
        lines_read = 0
        messages_dispatched = 0
        parse_errors = 0
        preserved_ids = []

        # Split preserving line discipline
        lines = raw_input.splitlines()

        for line_num, line in enumerate(lines, start=1):
            stripped = line.strip()
            if not stripped:
                continue

            lines_read += 1

            # 1. Framing & JSON Parsing
            try:
                msg = json.loads(stripped)
            except json.JSONDecodeError as exc:
                parse_errors += 1
                # Write diagnostic strictly to stderr
                self.stderr.write(
                    f"[DIAGNOSTIC] Line {line_num}: JSON parse failure: {exc.msg} at pos {exc.pos}\n"
                )
                # Write structured JSON-RPC error response to stdout
                error_response = {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {
                        "code": PARSE_ERROR_CODE,
                        "message": f"Parse error: Invalid JSON framing at line {line_num}"
                    }
                }
                self.stdout.write(json.dumps(error_response) + "\n")
                continue

            # 2. Protocol Validation & ID Preservation
            if not isinstance(msg, dict):
                parse_errors += 1
                self.stderr.write(f"[DIAGNOSTIC] Line {line_num}: Top-level entity must be JSON object\n")
                error_response = {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {
                        "code": INVALID_REQUEST_CODE,
                        "message": "Invalid Request: JSON payload must be an object"
                    }
                }
                self.stdout.write(json.dumps(error_response) + "\n")
                continue

            msg_id = msg.get("id")
            method = msg.get("method", "ping")
            params = msg.get("params")

            # Write processing diagnostic to stderr
            self.stderr.write(
                f"[DIAGNOSTIC] Line {line_num}: Dispatching method='{method}' id={msg_id!r}\n"
            )

            # 3. Backend Dispatch
            service_result = self.backend.call_service(method=method, params=params)
            messages_dispatched += 1
            preserved_ids.append(msg_id)

            # 4. Protocol Output to stdout
            response = {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": service_result
            }
            self.stdout.write(json.dumps(response) + "\n")

        # Capture stream lines
        stdout_content = self.stdout.getvalue().splitlines()
        stderr_content = self.stderr.getvalue().splitlines()

        return FramingExecutionReport(
            lines_read=lines_read,
            messages_dispatched=messages_dispatched,
            parse_errors_encountered=parse_errors,
            request_ids_preserved=preserved_ids,
            stdout_lines=stdout_content,
            stderr_lines=stderr_content
        )


def run_demonstration() -> Dict[str, Any]:
    """Execute demonstration covering 2 valid lines, malformed JSON line, and stderr diagnostics."""
    print("=" * 75)
    print("MCP stdio Transport Framing & Offline Adapter Extension (R49-T034)")
    print("=" * 75)

    backend = DeterministicLocalAdapter()
    processor = StdioFramingProcessor(backend=backend)

    # 1. Normal Case: Two complete lines -> Two complete messages
    two_lines_input = (
        '{"jsonrpc": "2.0", "id": 101, "method": "ping"}\n'
        '{"jsonrpc": "2.0", "id": "req-xyz-2", "method": "tools/list"}\n'
    )
    print("\n[Input 1: Two Complete Lines]")
    print(two_lines_input.strip())

    report_two_lines = processor.process_input(two_lines_input)
    print("\n[stdout Protocol Stream (Newline-Delimited JSON-RPC)]:")
    for out in report_two_lines.stdout_lines:
        print(f"  {out}")

    print("\n[stderr Diagnostic Stream]:")
    for err in report_two_lines.stderr_lines:
        print(f"  {err}")

    # 2. Boundary / Failure Case: Malformed JSON framing
    print("\n" + "-" * 75)
    processor_malformed = StdioFramingProcessor(backend=backend)
    malformed_input = (
        '{"jsonrpc": "2.0", "id": 303, "method": "ping"}\n'
        '{"malformed_json": missing_quotes_here\n'
    )
    print("[Input 2: Normal Line + Malformed Line]")
    print(malformed_input.strip())

    report_malformed = processor_malformed.process_input(malformed_input)
    print("\n[stdout Protocol Stream]:")
    for out in report_malformed.stdout_lines:
        print(f"  {out}")

    print("\n[stderr Diagnostic Stream]:")
    for err in report_malformed.stderr_lines:
        print(f"  {err}")

    print("\n" + "=" * 75)
    print("Real-service behaviors NOT established by this offline mock:")
    for idx, item in enumerate(REAL_SERVICE_BEHAVIORS_NOT_ESTABLISHED, start=1):
        print(f"  {idx}. {item}")
    print("=" * 75)

    return {
        "two_lines_messages_dispatched": report_two_lines.messages_dispatched,
        "two_lines_parse_errors": report_two_lines.parse_errors_encountered,
        "malformed_parse_errors": report_malformed.parse_errors_encountered,
        "diagnostics_in_stdout": any("[DIAGNOSTIC]" in l for l in report_two_lines.stdout_lines),
    }


if __name__ == "__main__":
    run_demonstration()
