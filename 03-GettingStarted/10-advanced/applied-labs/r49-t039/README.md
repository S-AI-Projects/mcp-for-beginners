# Applied Lab R49-T039: Low-Level Typed Tool Dispatch & Controlled Evaluation Experiment

**Student:** Ananya Andhare  
**Task ID:** R49-T039  
**Parent Module:** `03-GettingStarted/10-advanced`  
**Reference Document:** [03-GettingStarted/10-advanced/README.md](../../README.md)  

---

## 1. Overview & Pedagogical Objective

This lab extends the lessons in **Advanced Server Usage** (`03-GettingStarted/10-advanced`) by demonstrating:
1. **Low-Level Centralized Tool Dispatch:** Emulating the MCP low-level server pattern (`@server.call_tool`), where tool routing, allowlist enforcement (`{"add", "multiply"}`), and parameter validation are handled uniformly in a centralized gateway.
2. **Deterministic Schema & Fault Isolation:** Numeric parameter validation (`(int, float)`) rejecting malformed or non-allowlisted requests with JSON-RPC error codes `-32601` and `-32602` before invoking tool handlers.
3. **Controlled Evaluation Experiment:** Comparing three distinct controlled workload configurations (single-call, dual-tool pair, and mixed boundary batch) to analyze correctness, error containment, and architectural trade-offs.

---

## 2. Simulation & Mocking Boundaries

> [!NOTE]
> **Simulation Boundary:** This applied lab is a deterministic in-memory fixture evaluating low-level tool dispatch and parameter filtering. It does not spawn background processes, open network sockets, or make claims regarding real-world LLM accuracy or cloud latency.

---

## 3. Contract Specification

| Scenario | Input Request | Expected Response |
|---|---|---|
| Valid `add` | `{"id": 1, "tool": "add", "params": {"a": 2, "b": 3}}` | `{"id": 1, "result": {"value": 5, "tool": "add"}}` |
| Valid `multiply` | `{"id": 2, "tool": "multiply", "params": {"a": 2, "b": 3}}` | `{"id": 2, "result": {"value": 6, "tool": "multiply"}}` |
| Unknown Tool | `{"id": 3, "tool": "unauthorized_cmd", "params": {"a": 1, "b": 1}}` | `{"id": 3, "error": {"code": -32601, "message": "Method not found: Tool 'unauthorized_cmd' is not allowlisted."}}` |
| String Parameter `a` | `{"id": 4, "tool": "add", "params": {"a": "2", "b": 3}}` | `{"id": 4, "error": {"code": -32602, "message": "Invalid params: Parameter 'a' must be numeric, got str."}}` |
| Circuit Isolation | Malformed or unauthorized request | 0 tool handlers executed; execution counters unchanged. |

---

## 4. Evaluation Experiment & Trade-off Analysis

The experiment evaluates three controlled workload configurations:

| Configuration | Workload Size & Composition | Valid Passed | Filter Efficacy (Errors Caught) | Unauthorized Calls | Correctness | Architectural Trade-off |
|---|---|---|---|---|---|---|
| **Config 1: Minimal** | 1 call: `add(2, 3)` | 1 / 1 | N/A (0 invalid) | 0 | 100.0% | Minimal dispatch overhead; validates atomic execution without concurrency or cross-request pollution. |
| **Config 2: Standard Pair** | 2 calls: `add(2,3)`, `multiply(2,3)` | 2 / 2 | N/A (0 invalid) | 0 | 100.0% | Exercises complete allowlist; verifies handler separation with zero measurable performance degradation. |
| **Config 3: Mixed Batch** | 6 calls: 3 valid, 3 invalid (unknown tool, string param, missing param) | 3 / 3 | 3 / 3 (100% intercepted) | 0 | 100.0% | Assesses resilience under faulty/hostile inputs; confirms error handling halts execution without affecting subsequent valid calls. |

---

## 5. Verification & Test Execution

Run the demonstration script:
```bash
python3 03-GettingStarted/10-advanced/applied-labs/r49-t039/example.py
```

Run the unit test suite:
```bash
python3 -m unittest discover -s 03-GettingStarted/10-advanced/applied-labs/r49-t039 -p "test_*.py" -v
```
