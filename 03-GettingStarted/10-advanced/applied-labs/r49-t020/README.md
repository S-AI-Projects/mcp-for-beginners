# R49-T020: Typed Tool Dispatch — Scenario Assessment

## Purpose & Lesson Connection

In "Advanced server usage" (`03-GettingStarted/10-advanced`), low-level MCP servers dispatch tool requests and enforce strict schema boundaries. An advanced server must validate tool names against an allowlist and check argument types before invoking handlers.

This applied lab demonstrates:
1. Dispatching `add(a, b)` and `multiply(a, b)` via an allowlist (`add(2, 3)` $\rightarrow$ 5, `multiply(2, 3)` $\rightarrow$ 6).
2. Structured error envelopes for unknown tools and non-numeric argument types (e.g. string `a`).
3. Execution safety: a failed call never executes a fallback or alternative tool.
4. **Three Applied Assessment Questions** covering output prediction, failure diagnosis, and boundary policy decisions.

## Applied Scenario Questions & Factual Answers

1. **Predict Output**:
   - *Question*: What is the output of `add(2, 3)`?
   - *Answer*: `{"success": True, "tool": "add", "result": 5}`.
   - *Rationale*: Tool is allowlisted, arguments are valid numbers, operation returns exact sum.
2. **Diagnose Failure**:
   - *Question*: Why does calling `add` with arguments `{"a": "2", "b": 3}` fail?
   - *Answer*: `INVALID_ARGUMENT_TYPE`.
   - *Rationale*: Strict type checking prohibits string-to-numeric coercion to prevent arithmetic ambiguities.
3. **Boundary Policy**:
   - *Question*: How does the server handle unlisted tools like `divide`?
   - *Answer*: Rejection with `UNKNOWN_TOOL` without fallback execution.
   - *Rationale*: Fallback execution risks invoking unintended or mutating handlers.

## Running the Example

From the repository root:

```bash
python3 03-GettingStarted/10-advanced/applied-labs/r49-t020/example.py
```

### Expected Output

```text
=== Advanced Server Usage: Scenario Assessment (R49-T020) ===

[Standard Dispatches]
add(2, 3) -> {'success': True, 'tool': 'add', 'result': 5}
multiply(2, 3) -> {'success': True, 'tool': 'multiply', 'result': 6}

[Applied Questions & Executable Checks]
Q1 (Q1_predict_output): PASSED
   Question: What is the structured result when calling add(2, 3)?
   Response: {'success': True, 'tool': 'add', 'result': 5}
Q2 (Q2_diagnose_failure): PASSED
   Question: Why does calling add with arguments {'a': '2', 'b': 3} fail?
   Response: {'success': False, 'error': {'code': 'INVALID_ARGUMENT_TYPE', 'message': "Argument 'a' must be numeric, got str"}}
Q3 (Q3_boundary_policy): PASSED
   Question: What boundary policy governs unlisted tools like 'divide'?
   Response: {'success': False, 'error': {'code': 'UNKNOWN_TOOL', 'message': "Tool 'divide' is not in allowlist: ['add', 'multiply']"}}

All scenario checks passed. Failed calls returned structured errors without side effects.
```

## Running the Unit Tests

```bash
python3 -m unittest discover -s 03-GettingStarted/10-advanced/applied-labs/r49-t020 -p "test_*.py"
```

## Scope and Limitations

This is a local contract fixture. It does not implement full wire-level MCP transport framing or network communication.
