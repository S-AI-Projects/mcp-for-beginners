# Applied Lab R49-T040: Advanced Topics Runnable Concept Example & Architectural Mapping

**Student:** Ananya Andhare  
**Task ID:** R49-T040  
**Parent Module:** `05-AdvancedTopics`  
**Reference Document:** [05-AdvancedTopics/README.md](../../README.md)  

---

## 1. Overview & Pedagogical Objective

This lab extends **Advanced Topics in MCP** (`05-AdvancedTopics`) by implementing a minimal complete runnable local example of typed tool dispatch. It maps every public input and output directly to foundational concepts covered in the advanced topics curriculum:
- **Lesson 5.5 (Routing) & Lesson 5.8 (Security):** Tool allowlisting (`{"add", "multiply"}`) enforcing the Principle of Least Privilege.
- **Lesson 5.8 (Security) & Lesson 5.16 (Protocol Features):** Strict numeric parameter schema validation, graceful error framing, and input sanitization.
- **Lesson 5.7 (Scaling) & Lesson 5.8 (Security):** Circuit isolation preventing partial execution or state corruption upon invalid requests.

---

## 2. Simulation & Mocking Boundaries

> [!NOTE]
> **Simulation Boundary:** This applied lab is a deterministic in-memory contract fixture demonstrating low-level routing, schema verification, and JSON-RPC 2.0 error framing. It does not interface with real-world LLMs, external cloud providers, or GPUs, ensuring complete isolation and reproducible test execution.

---

## 3. Contract Specification

| Scenario | Input Request | Expected Response |
|---|---|---|
| Valid `add` | `{"id": 1, "tool": "add", "params": {"a": 2, "b": 3}}` | `{"id": 1, "result": {"value": 5, "tool": "add"}}` |
| Valid `multiply` | `{"id": 2, "tool": "multiply", "params": {"a": 2, "b": 3}}` | `{"id": 2, "result": {"value": 6, "tool": "multiply"}}` |
| Unknown Tool | `{"id": 3, "tool": "unauthorized_tool", "params": {"a": 1, "b": 1}}` | `{"id": 3, "error": {"code": -32601, "message": "Method not found: Tool 'unauthorized_tool' is not allowlisted."}}` |
| String Parameter `a` | `{"id": 4, "tool": "add", "params": {"a": "2", "b": 3}}` | `{"id": 4, "error": {"code": -32602, "message": "Invalid params: Parameter 'a' must be numeric (int or float), got str."}}` |
| Circuit Isolation | Malformed request or invalid tool call | Exactly 0 handler functions executed; execution counts remain unaltered. |

---

## 4. Public Input/Output to Lesson Concept Mapping

| Public Input / Output | Lesson Concept | Architectural Rationale |
|---|---|---|
| **Input:** `tool: 'add' / 'multiply'` | **5.5 Routing & 5.8 Security** (Principle of Least Privilege) | Restricts tool execution strictly to an explicit allowlist before parameter processing, preventing reflection attacks and unauthorized method execution. |
| **Input:** `params: {'a': num, 'b': num}` | **5.8 Security & 5.16 Protocol Features** (Schema Validation) | Enforces numeric types prior to invoking tool logic, preventing type-coercion bugs, SQL/command injection, and runtime panics. |
| **Output:** `{'result': {'value': 5, ...}}` | **5.16 Protocol Features** (JSON-RPC 2.0 Envelope) | Wraps computed responses in standard JSON-RPC 2.0 envelopes while preserving request IDs across asynchronous communication boundaries. |
| **Output:** `{'error': {'code': -32601, ...}}` | **5.8 Security & 5.16 Protocol Features** (Method Resolution Error) | Standardized error code for unallowlisted methods without leaking internal server architecture or stack traces. |
| **Output:** `{'error': {'code': -32602, ...}}` | **5.16 Protocol Features** (Defensive Parameter Error Envelope) | Informs client/agent of parameter schema mismatch, enabling automated retry/correction without severing transport sessions. |
| **Invariant:** Failed calls execute 0 tools | **5.7 Scaling & 5.8 Security** (Circuit Isolation) | Guarantees that validation failures immediately abort execution, avoiding side effects or state corruption. |

---

## 5. Verification & Test Execution

Run the demonstration script:
```bash
python3 05-AdvancedTopics/applied-labs/r49-t040/example.py
```

Run the unit test suite:
```bash
python3 -m unittest discover -s 05-AdvancedTopics/applied-labs/r49-t040 -p "test_*.py" -v
```
