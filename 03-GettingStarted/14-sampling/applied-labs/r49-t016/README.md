# R49-T016: Client-Consent Gate — Refactor the Teaching Example

## Purpose & Lesson Connection

In "Sampling - delegate features to the Client" (`03-GettingStarted/14-sampling`), the server delegates LLM completion tasks to the host client via sampling requests. Because invoking client-side models consumes user quotas and may disclose contextual data, hosts require explicit client-consent gating.

This applied lab represents client-side sampling consent as a state machine:
- **Pending**: Request created, waiting for user decision.
- **Approved**: User consented; the model stub is called exactly once.
- **Denied**: User declined; the model stub is never called (0 invocations).
- **Immutability**: Completed requests (approved or denied) cannot be re-evaluated.

## Refactoring and Equivalence

- **Baseline Implementation**: A monolithic `BaselineConsentGate` handles state, policy decisions, and model dispatch in one class.
- **Refactored Implementation**: Extracts state transitions and immutability validation into a dedicated `ConsentStateMachine`.
- **Equivalence Proof**: Automated checks verify before-and-after behavioral parity across approved, denied, and re-approval boundary cases.

## Running the Example

From the repository root:

```bash
python3 03-GettingStarted/14-sampling/applied-labs/r49-t016/example.py
```

### Expected Output

```text
=== Client-Consent Gate State Machine (R49-T016) ===
Equivalence between Baseline and Refactored Gate: True
Approved Execution Result: {'state': 'approved', 'response': 'Echo: Generate product description', 'model_calls': 1}
Denied Execution Result: {'state': 'denied', 'response': None, 'model_calls': 0}
Re-approval Blocked for Completed Request: True

Demo completed. Denied consent made 0 model calls; approved consent made 1 call.
```

## Running the Unit Tests

```bash
python3 -m unittest discover -s 03-GettingStarted/14-sampling/applied-labs/r49-t016 -p "test_*.py"
```

## Scope and Limitations

This is a local state machine simulation. It does not communicate with real OpenAI, GitHub Copilot, or Anthropic LLM endpoints.
