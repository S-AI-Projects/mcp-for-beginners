# Applied Lab R49-T031: Capability Negotiation & Boundary-Case Feature Gating

**Lab Extension for**: `11-MCPServerHandsOnLabs/07-Semantic-Search`  
**Task ID**: `R49-T031` (Issue #31)  
**Author**: Ananya Andhare  

---

## 🎯 Objective & Lesson Focus

In a production Model Context Protocol (MCP) deployment, clients and servers exchange supported capabilities during the `initialize` handshake. This lesson extension explores **capability discovery, set intersection, and strict pre-dispatch feature gating** within a semantic search server.

### Key Lesson Insights:
1. **Bilateral Negotiation**: The active capability set is strictly the mathematical intersection:
   $$\text{Negotiated} = \text{Client Capabilities} \cap \text{Server Capabilities}$$
2. **Pre-Dispatch Feature Gating**: If a client invokes an operation belonging to a capability that was not successfully negotiated, the server/session must reject the call **before dispatch**—aborting before looking up or executing any handler.
3. **Defense Against Capability Drift**: Even if the server contains private handler logic for an unnegotiated capability (e.g., `resources`), pre-dispatch gating guarantees that the handler cannot be reached.

---

## 🔬 Boundary Decision Analysis

| Scenario | Client Capabilities | Server Capabilities | Negotiated Set | Invocations Tested | Exact Boundary Decision |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Smallest Valid Case** | `{"tools"}` | `{"tools"}` | `{"tools"}` | `tools/semantic_search` | Minimal valid configuration. Invocation succeeds against the fixture. |
| **Boundary Case: Asymmetric (Primary)** | `{"tools", "resources"}` | `{"tools", "prompts"}` | `{"tools"}` | 1. `tools/semantic_search`<br>2. `resources/read_product`<br>3. `prompts/search_prompt` | `tools` is negotiated and dispatches. `resources` is offered by client but unsupported by server; calling it raises `CapabilityNotNegotiatedError` before dispatch. `prompts` is supported by server but not requested by client; calling it is likewise rejected. |
| **Boundary Case: Disjoint** | `{"resources"}` | `{"tools"}` | `∅` (empty) | Any capability call | Disjoint sets negotiate to an empty set. Every dispatch attempt is rejected before execution. |
| **Boundary Case: Empty Set** | `∅` | `{"tools", "prompts"}` | `∅` (empty) | Any capability call | Client declaring no capabilities yields an empty session; zero calls permitted. |
| **Invalid Case: Format / Unknown** | `{"tools"}` | `{"tools"}` | `{"tools"}` | `""` (empty) or unknown method | Empty capability raises `InvalidCapabilityError`; unknown method under negotiated tool raises `UnknownMethodError`. |

### Why Pre-Dispatch Rejection is Crucial
If capability checks occur *after* dispatch or inside individual tool handlers, errors manifest as unhandled execution exceptions, state leaks, or security vulnerabilities (invoking internal resources without mutual consent). Pre-dispatch validation guarantees that unsupported requests fail fast with clean protocol error semantics.

---

## 📦 Scope, Simplifications & Limitations

> [!NOTE]
> **Deterministic Simulation Label**: To ensure reproducibility and zero external dependencies:
> - **Local Fixture**: Uses a hardcoded 4-item outdoor retail catalog (`LOCAL_FIXTURE_PRODUCTS`).
> - **Simulated Semantic Similarity**: Computes token-based cosine similarity using the Python standard library (`math`, `re`).
> - **Zero External Services**: Requires no Azure OpenAI API keys, pgvector database, GPUs, or network connectivity.
> - **Hardware & Model Claims**: This fixture makes no claims regarding real cloud service availability, embedding latency, or large-scale transformer accuracy. It is designed specifically to test protocol conformance and capability negotiation logic.

---

## 🚀 Execution & Verification

### Prerequisites
- Python 3 standard library (`sys`, `math`, `unittest`, `dataclasses`).

### 1. Run Interactive Demonstration
```bash
python3 11-MCPServerHandsOnLabs/07-Semantic-Search/applied-labs/r49-t031/example.py
```

**Expected Output**:
```text
======================================================================
MCP Capability Negotiation & Boundary-Case Extension (R49-T031)
======================================================================

[Scenario 1: Asymmetric Negotiation]
  Client declared  : ['resources', 'tools']
  Server supported : ['prompts', 'tools']
  Negotiated set   : ['tools']
  Client-unsupported: ['resources']

  Invoking negotiated capability 'tools/semantic_search'...
  -> Success! Found 2 items:
     - Trail Runner Pro Shoes (score: 0.822)
     - Ultra Lightweight Road Shoes (score: 0.4167)

  Invoking unnegotiated capability 'resources/read_product'...
  -> Correctly rejected before dispatch!
     Reason: Capability 'resources' is not negotiated for this session. Negotiated set: ['tools']. Client offered: ['resources', 'tools'], Server offered: ['prompts', 'tools']. Invocation rejected before dispatch.

======================================================================
All scenarios completed successfully.
======================================================================
```

### 2. Run Automated Unit Tests
```bash
python3 -m unittest discover -s 11-MCPServerHandsOnLabs/07-Semantic-Search/applied-labs/r49-t031 -p "test_*.py" -v
```

**Expected Result**:
```text
Ran 10 tests in 0.001s

OK
```

### 3. Run Automated Check and Evidence Generation
```bash
python3 work/R49-T031/check.py
```
This generates:
- `work/R49-T031/tool_versions.txt`
- `work/R49-T031/inputs.json`
- `work/R49-T031/results.json`
Exits with code `0` on success, or non-zero on assertion failure.
