# Applied Lab R49-T032: Capability Negotiation — Comparing Two Approaches

**Lab Extension for**: `11-MCPServerHandsOnLabs/01-Architecture`  
**Task ID**: `R49-T032` (Issue #32)  
**Author**: Ananya Andhare  

---

## 🎯 Objective & Architectural Context

In **Layer 1 (Protocol Layer)** of an MCP architecture, capability negotiation establishes the contract between client and server. This applied lab explores and compares two distinct architectural patterns for capability negotiation and feature gating:

1. **Approach 1: Direct Stateful Implementation**
   - Implements a stateful protocol session (`DirectMCPServer` & `DirectMCPSession`).
   - Dynamically intersects declared sets at handshake time: `client_capabilities ∩ server_capabilities`.
   - Enforces **pre-dispatch feature gating**: intercepts calls before handler lookup and raises `CapabilityNotNegotiatedError` if unnegotiated.
2. **Approach 2: Independent Calculation & Explicit Truth Table**
   - Independent pure mathematical calculation: `{c for c in client if c in server}`.
   - Explicit static truth table mapping canonical capability input pairs to pre-determined negotiation and dispatch permissions (`EXPLICIT_EXPECTED_TABLE`).

---

## 📊 Comparative Analysis: Side-by-Side Equivalence

Both approaches are evaluated against **identical inputs**:

| Scenario | Client Capabilities | Server Capabilities | Approach 1: Direct | Approach 2a: Calc | Approach 2b: Truth Table | Equivalence | Pre-Dispatch Rejection |
| :--- | :--- | :--- | :--- | :--- | :--- | :---: | :--- |
| **Primary (Asymmetric)** | `{"tools", "resources"}` | `{"tools", "prompts"}` | `["tools"]` | `["tools"]` | `["tools"]` | **MATCH** | Calling `resources` rejected before dispatch (0 calls). |
| **Smallest Valid** | `{"tools"}` | `{"tools"}` | `["tools"]` | `["tools"]` | `["tools"]` | **MATCH** | Valid `tools` call succeeds on store fixture. |
| **Disjoint** | `{"resources"}` | `{"tools"}` | `[]` (empty) | `[]` (empty) | `[]` (empty) | **MATCH** | Any call rejected before dispatch. |
| **Empty Client** | `∅` | `{"tools", "prompts"}` | `[]` (empty) | `[]` (empty) | `[]` (empty) | **MATCH** | Zero capabilities permitted. |

### Architectural Trade-offs

| Criterion | Approach 1: Direct Implementation | Approach 2: Independent Table / Calc |
| :--- | :--- | :--- |
| **Primary Role** | Runtime protocol dispatch engine | Specification verification & golden test fixture |
| **Statefulness** | Stateful (`DirectMCPSession`, handler call metrics) | Purely functional / stateless lookup |
| **Extensibility** | Dynamic handler registration at runtime | Requires manual table schema updates |
| **Failure Safety** | Pre-dispatch gate prevents internal handler exposure | High mathematical clarity, no execution gate |

---

## 📦 Scope, Simplifications & Mock Disclaimers

> [!NOTE]
> **Deterministic Simulation Label**:
> - **Local Fixture**: Uses a hardcoded 3-store retail analytics fixture (`LOCAL_FIXTURE_STORES`) matching the Zava Retail Analytics theme of Lab 01.
> - **Zero External Services**: Pure standard library (`sys`, `unittest`, `dataclasses`, `json`). Requires no PostgreSQL database, network connection, cloud credentials, or GPU hardware.
> - **Hardware / Service Disclaimers**: Makes no claims about real database connection latency, pooling scalability, or enterprise throughput. Focuses strictly on protocol-level capability negotiation and pre-dispatch gating correctness.

---

## 🚀 Execution & Verification

### 1. Interactive Comparison Demonstration
```bash
python3 11-MCPServerHandsOnLabs/01-Architecture/applied-labs/r49-t032/example.py
```

### 2. Automated Unit Tests
```bash
python3 -m unittest discover -s 11-MCPServerHandsOnLabs/01-Architecture/applied-labs/r49-t032 -p "test_*.py" -v
```
**Expected Result**:
```text
Ran 9 tests in 0.001s

OK
```

### 3. Automated Check and Evidence Generation
```bash
python3 work/R49-T032/check.py
```
Outputs:
- `work/R49-T032/tool_versions.txt`
- `work/R49-T032/inputs.json`
- `work/R49-T032/results.json`
- `work/R49-T032/comparison_table.json`
