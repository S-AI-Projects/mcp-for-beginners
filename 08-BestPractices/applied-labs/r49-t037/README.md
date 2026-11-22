# Applied Lab R49-T037: Typed Tool Dispatch and Applied Scenario Assessment

**Student:** Ananya Andhare  
**Task ID:** R49-T037  
**Parent Module:** `08-BestPractices`  
**Reference Document:** [08-BestPractices/README.md](../../README.md)  

---

## 1. Overview & Pedagogical Objective

This lab extends the lessons in **MCP Development Best Practices** (`08-BestPractices`) by demonstrating two critical server architecture patterns:
1. **Strict Input Validation & Defense-in-Depth:** An explicit tool allowlist (`{"add", "multiply"}`) and strict numeric argument type enforcement (`int` or `float`, disallowing `bool`), halting processing immediately with standard JSON-RPC error envelopes (`-32601`, `-32602`) before any tool execution occurs.
2. **Applied Scenario Assessment:** A formal framework of three applied scenario questions covering output prediction, failure diagnosis, and boundary policy decisions, each paired with an explicit factual rationale and automated executable regression check.

---

## 2. Simulation & Mocking Boundaries

> [!NOTE]
> **Simulation Boundary:** This applied lab is a standalone deterministic contract fixture. It simulates JSON-RPC tool dispatch and parameter validation in memory without network sockets, stdio pipe serialization, or remote LLM integrations. It focuses entirely on execution isolation, input sanitization, and structured failure handling.

---

## 3. Contract Specification

| Scenario | Input Request | Expected Outcome / Error Envelope |
|---|---|---|
| Valid `add` | `{"id": 1, "tool": "add", "params": {"a": 2, "b": 3}}` | `{"id": 1, "result": {"value": 5, "tool": "add"}}` |
| Valid `multiply` | `{"id": 2, "tool": "multiply", "params": {"a": 2, "b": 3}}` | `{"id": 2, "result": {"value": 6, "tool": "multiply"}}` |
| Unknown Tool | `{"id": 3, "tool": "subtract", "params": {"a": 5, "b": 2}}` | `{"id": 3, "error": {"code": -32601, "message": "Method not found: Tool 'subtract' is not allowlisted."}}` |
| Non-numeric Argument | `{"id": 4, "tool": "add", "params": {"a": "2", "b": 3}}` | `{"id": 4, "error": {"code": -32602, "message": "Invalid params: Parameter 'a' must be numeric (int or float), got str."}}` |
| Circuit Isolation | Malformed request or invalid tool call | Zero tools executed; no fallback or cascading side effects. |

---

## 4. Applied Questions & Rationales

### Q1: Predict an Output
- **Question:** What is the exact JSON-RPC response when calling tool `add` with float values `a=2.5` and `b=-0.5` under `id=10`?
- **Factual Answer:** `{"jsonrpc": "2.0", "id": 10, "result": {"value": 2.0, "tool": "add"}}`
- **Rationale:** Both `2.5` and `-0.5` satisfy numeric type validation (`(int, float)`). The `add` handler calculates `2.5 + (-0.5) = 2.0`. The response wraps the computation in a standard success envelope while preserving request ID `10`.
- **Executable Check:** `check_q1_predict_output()` in `example.py`.

### Q2: Diagnose a Failure
- **Question:** Given request `{"id": 20, "tool": "multiply", "params": {"a": "3", "b": 4}}`, why does it fail and how many handlers execute?
- **Factual Answer:** Error code `-32602` (`INVALID_PARAMS`), exactly `0` handlers executed.
- **Rationale:** The parameter `a` is a string (`"3"`). The schema validator rejects string values before dispatch to prevent type coercion vulnerabilities. Because validation fails prior to execution, zero handler functions are invoked and no state changes occur.
- **Executable Check:** `check_q2_diagnose_failure()` in `example.py`.

### Q3: Choose a Boundary Policy
- **Question:** When an unauthorized or unallowlisted tool is requested, should the server fallback to a default tool or immediately reject?
- **Factual Answer:** `REJECT_IMMEDIATELY_NO_FALLBACK`
- **Rationale:** Under the Principle of Least Privilege and safe MCP server design, unknown methods must fail fast with code `-32601` (`METHOD_NOT_FOUND`). Executing fallback tools risks unintended execution side effects, privilege escalation, and semantic divergence.
- **Executable Check:** `check_q3_boundary_policy()` in `example.py`.

---

## 5. Verification & Test Execution

Run the demonstration script:
```bash
python3 08-BestPractices/applied-labs/r49-t037/example.py
```

Run the unit test suite:
```bash
python3 -m unittest discover -s 08-BestPractices/applied-labs/r49-t037 -p "test_*.py" -v
```
