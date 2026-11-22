# Applied Lab R49-T035: Typed Tool Dispatch, Allowlist Authorization & Regression Checks

**Lab Extension for**: `11-MCPServerHandsOnLabs/05-MCP-Server`  
**Task ID**: `R49-T035` (Issue #35 / Task 5)  
**Author**: Ananya Andhare  

---

## 🎯 Objective & Architectural Context

In an enterprise Model Context Protocol (MCP) server, robust tool execution requires **strict allowlist authorization**, **typed argument schema validation**, and **execution isolation**. This applied lab implements and formally tests these principles:

1. **Explicit Allowlist**: The server exclusively allows registered arithmetic tools: `{"add", "multiply"}`.
2. **Type Enforcement**: Parameter schema requires numeric inputs (`int` or `float`). Passing strings (e.g., `a: "2"`) or booleans triggers structured validation failures.
3. **Structured JSON-RPC Errors**:
   - Unknown tools return error code `-32601` (`Method not found`).
   - Invalid arguments return error code `-32602` (`Invalid params`).
4. **Execution Isolation (Circuit Breaker)**: A failed tool invocation halts immediately without executing fallback tools or corrupting server state.
5. **Regression Verification**: Publishes an exact worked input-to-output reference matrix executed as automated regression tests.

---

## 🔬 Worked Input-to-Output Reference Table

| Case | Input Payload | Step-by-Step Validation & Execution | Structured Response | Execution Count |
| :--- | :--- | :--- | :--- | :---: |
| **Valid Add** | `{"id": 1, "tool": "add", "params": {"a": 2, "b": 3}}` | 1. Allowlist: `add` $\in$ allowlist $\rightarrow$ **OK**<br>2. Type validation: `a=2` (int), `b=3` (int) $\rightarrow$ **OK**<br>3. Compute: $2 + 3 = 5$ | `{"id": 1, "result": {"value": 5, "tool": "add"}}` | `add`: 1<br>`multiply`: 0 |
| **Valid Multiply** | `{"id": 2, "tool": "multiply", "params": {"a": 2, "b": 3}}` | 1. Allowlist: `multiply` $\in$ allowlist $\rightarrow$ **OK**<br>2. Type validation: `a=2` (int), `b=3` (int) $\rightarrow$ **OK**<br>3. Compute: $2 \times 3 = 6$ | `{"id": 2, "result": {"value": 6, "tool": "multiply"}}` | `add`: 1<br>`multiply`: 1 |
| **Unknown Tool** | `{"id": 3, "tool": "power", "params": {"a": 2, "b": 3}}` | 1. Allowlist: `power` $\notin$ allowlist $\rightarrow$ **FAIL**<br>2. Execution: Aborted immediately | `{"id": 3, "error": {"code": -32601, "message": "Method not found..."}}` | `add`: 1<br>`multiply`: 1 *(no change)* |
| **Invalid Param (String `a`)** | `{"id": 4, "tool": "add", "params": {"a": "2", "b": 3}}` | 1. Allowlist: `add` $\in$ allowlist $\rightarrow$ **OK**<br>2. Type validation: `a='2'` (str $\neq$ num) $\rightarrow$ **FAIL**<br>3. Execution: Aborted immediately | `{"id": 4, "error": {"code": -32602, "message": "Invalid params..."}}` | `add`: 1<br>`multiply`: 1 *(no change)* |

---

## 📦 Scope, Simplifications & Mock Disclaimers

> [!NOTE]
> **Deterministic Simulation Label**:
> - **Local Contract Fixture**: This module models tool dispatch and argument validation logic. It is not a complete network transport layer.
> - **Zero External Services**: Pure standard library Python (`dataclasses`, `typing`, `unittest`, `json`). Requires no PostgreSQL database, asyncpg driver, external cloud APIs, or GPU hardware.
> - **Performance Disclaimers**: Makes no claims about production database connection pool latency or FastMCP async task scheduling.

---

## 🚀 Execution & Verification

### 1. Interactive Worked Demonstration
```bash
python3 11-MCPServerHandsOnLabs/05-MCP-Server/applied-labs/r49-t035/example.py
```

### 2. Automated Unit Tests
```bash
python3 -m unittest discover -s 11-MCPServerHandsOnLabs/05-MCP-Server/applied-labs/r49-t035 -p "test_*.py" -v
```

**Expected Result**:
```text
Ran 8 tests in 0.001s

OK
```

### 3. Automated Check and Evidence Generation
```bash
python3 work/R49-T035/check.py
```
Generates:
- `work/R49-T035/tool_versions.txt`
- `work/R49-T035/inputs.json`
- `work/R49-T035/results.json`
- `work/R49-T035/regression_report.json`
Exits with code `0` on success.
