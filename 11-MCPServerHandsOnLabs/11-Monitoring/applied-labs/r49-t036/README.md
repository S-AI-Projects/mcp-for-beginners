# Applied Lab R49-T036: Trace Aggregation & Refactored Observability Architecture

**Lab Extension for**: `11-MCPServerHandsOnLabs/11-Monitoring`  
**Task ID**: `R49-T036` (Issue #36 / Task 6)  
**Author**: Ananya Andhare  

---

## 🎯 Objective & Architectural Context

Effective observability in an MCP server requires aggregating asynchronous trace events into coherent request summaries while respecting data privacy and handling partial lifecycle failures. This applied lab implements and formally verifies:

1. **Correlation & Trace Aggregation**: Groups raw event records by `request_id`, computing duration, counting tool invocations, and determining terminal status.
2. **Strict Privacy (Prompt Omission)**: In accordance with enterprise privacy guidelines, user prompts and input text are strictly stripped from telemetry summaries.
3. **Incomplete Trace Handling**: Requests missing terminal `end` events are classified as `INCOMPLETE` with `duration_ms: None` rather than incorrectly assigning `0`.
4. **Refactoring & Single-Responsibility Principle**:
   - **Baseline Implementation (`BaselineTraceAggregator`)**: Monolithic aggregation handling grouping, calculation, and redaction in one unit.
   - **Extracted Responsibility (`TraceLifecycleClassifier`)**: Dedicated component specializing in timestamp correlation, incomplete trace detection, and lifecycle evaluation.
   - **Refactored Aggregator (`RefactoredTraceAggregator`)**: Clean coordinator delegating lifecycle evaluation to the extracted classifier.
   - **Proven Equivalence**: Both implementations are proven 100% equivalent across the fixture.

---

## 🔬 Trace Aggregation Summary Matrix

| Request ID | Event Sequence | Evaluated Status | Duration | Tool Calls | Prompt Redaction | Notes |
| :--- | :--- | :---: | :---: | :---: | :---: | :--- |
| **`req-A`** | `start(100)` $\rightarrow$ `tool_1(104)` $\rightarrow$ `tool_2(108)` $\rightarrow$ `end(112)` | **SUCCESS** | **12 ms** | **2** | **Redacted** | Normal successful execution with 2 tool calls. |
| **`req-B`** | `start(200)` $\rightarrow$ `error(205)` $\rightarrow$ `end(205)` | **FAILURE** | **5 ms** | **0** | **Redacted** | Fails with `"Database connection timeout"`. |
| **`req-C`** | `start(300)` $\rightarrow$ `tool(305)` *(no end)* | **INCOMPLETE** | **None** | **1** | **Redacted** | Missing end event; duration is `None` (not 0). |

---

## 📦 Scope, Simplifications & Mock Disclaimers

> [!NOTE]
> **Deterministic Simulation Label**:
> - **Local Trace Fixture**: Uses a hardcoded 4-event sequence (`LOCAL_TRACE_FIXTURE`) representing canonical lifecycle stages.
> - **Zero External Telemetry Services**: Implemented using pure Python standard library (`json`, `dataclasses`, `unittest`). Requires no Azure Monitor, OpenTelemetry collector, Application Insights credentials, or cloud networking.
> - **Performance Disclaimers**: Focuses on trace aggregation logic and data privacy. Makes no claims regarding real-time event streaming throughput or distributed span propagation.

---

## 🚀 Execution & Verification

### 1. Interactive Demonstration
```bash
python3 11-MCPServerHandsOnLabs/11-Monitoring/applied-labs/r49-t036/example.py
```

### 2. Automated Unit Tests
```bash
python3 -m unittest discover -s 11-MCPServerHandsOnLabs/11-Monitoring/applied-labs/r49-t036 -p "test_*.py" -v
```

**Expected Result**:
```text
Ran 7 tests in 0.001s

OK
```

### 3. Automated Check and Evidence Generation
```bash
python3 work/R49-T036/check.py
```
Generates:
- `work/R49-T036/tool_versions.txt`
- `work/R49-T036/inputs.json`
- `work/R49-T036/results.json`
- `work/R49-T036/equivalence_report.json`
Exits with code `0` on success.
