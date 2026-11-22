# Applied Lab R49-T034: stdio Transport Message Framing & Offline Service Adapter

**Lab Extension for**: `03-GettingStarted/05-stdio-server`  
**Task ID**: `R49-T034` (Issue #34 / Task 4)  
**Author**: Ananya Andhare  

---

## 🎯 Objective & Transport Contract

The Model Context Protocol (MCP) standardizes standard input/output (`stdio`) as the primary transport mechanism for local server processes. This lab extension implements and verifies the core framing, request correlation, and stream-separation rules:

1. **Newline-Delimited Framing (NDJSON)**: Reads newline-delimited JSON-RPC messages from standard input. Exactly **two complete lines yield two complete messages**.
2. **Request ID Preservation**: Every response retains the precise `id` supplied in the client request (e.g., integers, UUIDs, or strings).
3. **Structured Parse Failure**: Malformed JSON input triggers an immediate structured JSON-RPC error response (`code: -32700`) written to `stdout`.
4. **Strict Stream Separation (Keep Diagnostics out of Protocol Stream)**:
   - `stdout` is reserved **exclusively** for valid JSON-RPC protocol messages.
   - Diagnostic statements, logs, and stack traces are directed strictly to `stderr`.
5. **Callable Service Interface & Deterministic Adapter**: Puts external dependencies behind `ExternalServiceBackend` with an offline deterministic implementation (`DeterministicLocalAdapter`), requiring zero network, paid APIs, or GPU hardware.

---

## 🔬 Protocol Stream Separation Architecture

```
                    ┌─────────────────────────┐
                    │ Client Input Stream     │
                    │ (Newline-Delimited JSON)│
                    └───────────┬─────────────┘
                                │
                                ▼
                    ┌─────────────────────────┐
                    │  StdioFramingProcessor  │
                    │   - JSON line parser    │
                    │   - ID preserver        │
                    │   - Callable Backend    │
                    └─────┬─────────────┬─────┘
                          │             │
       Protocol Messages  │             │ Diagnostic Logs
       (Pure JSON-RPC)    │             │ ([DIAGNOSTIC] ...)
                          ▼             ▼
                    ┌───────────┐ ┌───────────┐
                    │  stdout   │ │  stderr   │
                    └───────────┘ └───────────┘
```

---

## ⚠️ Real-Service Behaviors NOT Established by this Mock

While this local adapter establishes deterministic framing and protocol compliance, it explicitly **does not establish or simulate**:

1. **Network Latency & Handshake Overhead**: Zero simulation of TCP connection handshakes, TLS negotiation latency, or packet jitter.
2. **HTTP Transient Errors & Rate Limiting**: Does not establish HTTP 429 (Too Many Requests), 503 (Service Unavailable), or exponential retry backoff mechanisms.
3. **Socket Timeouts & Heartbeats**: Does not model dropped sockets, idle TCP keepalive timeouts, or connection reset errors.
4. **OS Pipe Buffer Saturation**: Does not simulate kernel pipe buffer limits (e.g., 64KB blocking writes) or process termination on `SIGPIPE`.
5. **Concurrent Multiplexing**: Processes messages sequentially line-by-line rather than concurrent asynchronous stream interleaving.

---

## 🚀 Execution & Verification

### 1. Interactive Demonstration
```bash
python3 03-GettingStarted/05-stdio-server/applied-labs/r49-t034/example.py
```

**Expected Output**:
```text
[stdout Protocol Stream (Newline-Delimited JSON-RPC)]:
  {"jsonrpc": "2.0", "id": 101, "result": {"status": "pong", "service": "local-offline-adapter", "version": "1.0.0"}}
  {"jsonrpc": "2.0", "id": "req-xyz-2", "result": {"tools": [{"name": "get_weather", "description": "Mock offline weather tool", "inputSchema": {"type": "object", "properties": {"city": {"type": "string"}}}}]}}

[stderr Diagnostic Stream]:
  [DIAGNOSTIC] Line 1: Dispatching method='ping' id=101
  [DIAGNOSTIC] Line 2: Dispatching method='tools/list' id='req-xyz-2'
```

### 2. Automated Unit Tests
```bash
python3 -m unittest discover -s 03-GettingStarted/05-stdio-server/applied-labs/r49-t034 -p "test_*.py" -v
```

**Expected Result**:
```text
Ran 7 tests in 0.001s

OK
```

### 3. Automated Check and Evidence Generation
```bash
python3 work/R49-T034/check.py
```
Generates:
- `work/R49-T034/tool_versions.txt`
- `work/R49-T034/inputs.json`
- `work/R49-T034/results.json`
- `work/R49-T034/stream_traces.json`
Exits with code `0` on success.
