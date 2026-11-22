# Applied Lab R49-T038: Typed Tool Dispatch, Failure Analysis & State Recovery

**Student:** Ananya Andhare  
**Task ID:** R49-T038  
**Parent Module:** `11-MCPServerHandsOnLabs`  
**Reference Document:** [11-MCPServerHandsOnLabs/README.md](../../README.md)  

---

## 1. Overview & Pedagogical Objective

This lab extends the concepts in **MCP Server Hands-On Labs** (`11-MCPServerHandsOnLabs`) by demonstrating:
1. **Strict Input Schema Validation & Gating:** Enforcing an explicit allowlist (`{"add", "multiply"}`) and strict numeric argument typing (`int` or `float`, disallowing `bool`), intercepting malformed or unauthorized requests before tool execution.
2. **Deterministic Error Reporting:** Returning standard JSON-RPC error envelopes (`-32601` for method not found, `-32602` for invalid or missing parameters) with informative diagnostic explanations.
3. **Failure Isolation & Immediate Recovery:** Demonstrating that failed calls (such as missing required fields or type mismatches) do not corrupt server state, latch errors, or invoke unintended tools, allowing the server to immediately and cleanly process subsequent valid requests.

---

## 2. Simulation & Mocking Boundaries

> [!NOTE]
> **Simulation Boundary:** This applied lab provides a deterministic in-memory contract fixture simulating MCP JSON-RPC tool dispatch. It does not initiate network sockets, connect to live PostgreSQL instances, or invoke external LLMs. Its purpose is to verify error handling semantics, circuit isolation, and immediate failure recovery under deterministic conditions.

---

## 3. Contract Specification

| Scenario | Input Request | Expected Response |
|---|---|---|
| Valid `add` | `{"id": 1, "tool": "add", "params": {"a": 2, "b": 3}}` | `{"id": 1, "result": {"value": 5, "tool": "add"}}` |
| Valid `multiply` | `{"id": 2, "tool": "multiply", "params": {"a": 2, "b": 3}}` | `{"id": 2, "result": {"value": 6, "tool": "multiply"}}` |
| Unknown Tool | `{"id": 3, "tool": "unknown_tool", "params": {"a": 1, "b": 2}}` | `{"id": 3, "error": {"code": -32601, "message": "Method not found: Tool 'unknown_tool' is not allowlisted."}}` |
| String Argument `a` | `{"id": 4, "tool": "add", "params": {"a": "2", "b": 3}}` | `{"id": 4, "error": {"code": -32602, "message": "Invalid params: Parameter 'a' must be numeric (int or float), got str."}}` |
| Missing Argument `b` | `{"id": 5, "tool": "add", "params": {"a": 42}}` | `{"id": 5, "error": {"code": -32602, "message": "Invalid params: Missing required parameter 'b'."}}` |
| Circuit Isolation | Any failed invocation | Exactly 0 handler functions executed; execution counts remain unaltered. |

---

## 4. Failure and Recovery Workflow

The lab demonstrates resilience across a four-step transaction sequence:
1. **Step 1 (Baseline Valid Call):**  
   Request `add(2, 3)` succeeds with result `5`.
2. **Step 2 (Documented Missing-Data Failure):**  
   Request `add(a=42)` omits parameter `b`. The validator intercepts the request, generates error `-32602`, and avoids invoking any handler.
3. **Step 3 (Documented Invalid-Data Failure):**  
   Request `add(a="2", b=3)` provides string `a`. The validator rejects type non-conformance with error `-32602`.
4. **Step 4 (Immediate Clean Recovery):**  
   Request `multiply(2, 3)` is submitted immediately following the failures. The server processes the request cleanly, returning `6` without requiring a restart or reset.

---

## 5. Verification & Test Execution

Run the demonstration:
```bash
python3 11-MCPServerHandsOnLabs/applied-labs/r49-t038/example.py
```

Run the unit test suite:
```bash
python3 -m unittest discover -s 11-MCPServerHandsOnLabs/applied-labs/r49-t038 -p "test_*.py" -v
```
