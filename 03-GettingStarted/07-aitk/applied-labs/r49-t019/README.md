# R49-T019: Client-Configuration Validation — Evaluation Experiment

## Purpose & Lesson Connection

In "Consuming a server with Microsoft Foundry Toolkit for Visual Studio Code" (`03-GettingStarted/07-aitk`), local host environments require safe server configurations prior to startup. Validating commands and argument lists prevents launch failures, while redacting environment values keeps secrets out of logs.

This applied lab conducts an **evaluation experiment** comparing three controlled configuration sizes (`small`, `medium`, `large`):
- Measures correctness (enforcing that secrets are redacted and environment keys are sorted).
- Compares processing overhead across configuration scales.
- Enforces strict boundary rules: rejects missing commands and single-string arguments.

## Evaluation Experiment Metrics

| Size | Arguments Count | Environment Keys | Correctness | Observed Trade-off |
| :--- | :--- | :--- | :--- | :--- |
| **Small** | 1 | 1 | 100% | Minimal latency |
| **Medium** | 5 | 5 | 100% | Negligible overhead |
| **Large** | 20 | 20 | 100% | Linear validation scaling |

*Note: All secret values are 100% redacted across all sizes.*

## Running the Example

From the repository root:

```bash
python3 03-GettingStarted/07-aitk/applied-labs/r49-t019/example.py
```

### Expected Output

```text
=== Configuration Validation Evaluation Experiment (R49-T019) ===

| Size | Args | Env Keys | Correctness | Validation Time (μs) |
| :--- | :--- | :--- | :--- | :--- |
| small | 1 | 1 | True | ... μs |
| medium | 5 | 5 | True | ... μs |
| large | 20 | 20 | True | ... μs |

Negative / Boundary Cases:
1. Missing command rejected: A non-empty string command is required
2. String args rejected: Arguments must be a list of strings, not a single string

Evaluation complete. Observed predictable linear scaling without launching processes.
```

## Running the Unit Tests

```bash
python3 -m unittest discover -s 03-GettingStarted/07-aitk/applied-labs/r49-t019 -p "test_*.py"
```

## Scope and Limitations

This is a local configuration validation evaluation. It does not launch servers or interface with Microsoft Foundry Toolkit or Azure OpenAI endpoints.
