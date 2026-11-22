# Applied Lab R49-T033: Simple Auth — Injected Verifier, State Invariants & Log Redaction

**Lab Extension for**: `03-GettingStarted/11-simple-auth`  
**Task ID**: `R49-T033` (Issue #33 / Task 3)  
**Author**: Ananya Andhare  

---

## 🎯 Objective & Architectural Context

Authentication in MCP requires verifying client credentials before dispatching tool or resource requests. This applied lab implements and validates a clean, three-stage authentication pipeline utilizing **verifier dependency injection**, **rigorous log redaction**, and **intermediate state invariant verification**:

1. **Injected Verifier Pattern**: The pipeline delegates credential verification to an injected `InjectedLocalVerifier`, enabling seamless swapping between local fixtures, mock providers, and production IdPs (e.g., Entra ID) without modifying request-processing logic.
2. **Three-Way Identity Differentiation**:
   - **Missing Token** $\rightarrow$ `unauthenticated` (verifier not invoked, no subject).
   - **Unknown Token** $\rightarrow$ `invalid` (verifier invoked, unrecognized credential, no subject).
   - **Known Token** $\rightarrow$ `subject` (verifier invoked, claims resolved, subject returned).
3. **Zero Token Log Exposure**: Under no circumstance is a raw bearer token value logged or persisted in plain text. Diagnostic logs use non-reversible SHA-256 fingerprints and explicit `[REDACTED]` masking.

---

## 🔬 Pipeline State Transition & Invariants

```
┌─────────────────────────────────┐
│     Incoming HTTP Headers       │
└────────────────┬────────────────┘
                 │
                 ▼
┌─────────────────────────────────┐
│       Step 1: EXTRACTION        │──► State 1: ExtractionState
│  Parses "Authorization: Bearer" │    (has_header, token_extracted, fingerprint)
└────────────────┬────────────────┘
                 │
                 ▼
┌─────────────────────────────────┐
│      Step 2: VERIFICATION       │──► State 2: VerificationState
│   Injected Verifier Execution   │    (verifier_invoked, token_recognized, claims_subject)
└────────────────┬────────────────┘
                 │
                 ▼
┌─────────────────────────────────┐
│      Step 3: RESOLUTION         │──► State 3: ResolutionState
│   Final Identity Determination  │    (final_status, resolved_subject, error_message)
└─────────────────────────────────┘
```

### Verified Mathematical Invariants

| Invariant Rule | Extraction Condition | Verification Condition | Guaranteed Final Output |
| :--- | :--- | :--- | :--- |
| **Missing Token** | `token_extracted == False` | `verifier_invoked == False` | `status == UNAUTHENTICATED`, `subject == None` |
| **Unknown Token** | `token_extracted == True` | `token_recognized == False` | `status == INVALID`, `subject == None` |
| **Known Token** | `token_extracted == True` | `token_recognized == True` | `status == AUTHENTICATED`, `subject == claims_subject` |
| **Log Sanitization** | Any input | Any verifier result | $\forall \text{ record} \in \text{logs}, \text{raw\_token} \notin \text{record}$ |

---

## 📦 Scope, Simplifications & Mock Disclaimers

> [!NOTE]
> **Deterministic Simulation Label**:
> - **Local Fixture**: Uses a hardcoded local dictionary fixture (`LOCAL_TOKEN_FIXTURE`) containing test tokens for `alice_andhare` and `bob_retail`.
> - **Zero External Services**: Pure Python standard library (`hashlib`, `re`, `enum`, `dataclasses`, `unittest`). No external JWT libraries, IdPs, cloud networks, or databases are required.
> - **Hardware / Service Disclaimers**: Makes no claims about real cryptographic signature speeds, OAuth 2.1 authorization server uptime, or key rotation latency. Focuses exclusively on identity resolution correctness and log redaction safety.

---

## 🚀 Execution & Verification

### 1. Interactive Pipeline Demonstration
```bash
python3 03-GettingStarted/11-simple-auth/applied-labs/r49-t033/example.py
```

**Expected Output**:
```text
[Scenario: Missing Token]
  Step 1 Extraction   : token_extracted=False, fingerprint=None
  Step 2 Verification : invoked=False, recognized=False, claims_sub=None
  Step 3 Resolution   : status=unauthenticated, subject=None
  Invariants Hold     : True

[Scenario: Invalid / Unknown Token]
  Step 1 Extraction   : token_extracted=True, fingerprint=39f6699a
  Step 2 Verification : invoked=True, recognized=False, claims_sub=None
  Step 3 Resolution   : status=invalid, subject=None
  Invariants Hold     : True

[Scenario: Valid Known Token (Alice)]
  Step 1 Extraction   : token_extracted=True, fingerprint=276be2c5
  Step 2 Verification : invoked=True, recognized=True, claims_sub=alice_andhare
  Step 3 Resolution   : status=authenticated, subject=alice_andhare
  Invariants Hold     : True

[Log Redaction Audit]
  Total log entries recorded : 7
  Raw token leaks detected   : 0 (Expected: 0)
```

### 2. Automated Unit Tests
```bash
python3 -m unittest discover -s 03-GettingStarted/11-simple-auth/applied-labs/r49-t033 -p "test_*.py" -v
```

**Expected Result**:
```text
Ran 7 tests in 0.000s

OK
```

### 3. Automated Check and Evidence Generation
```bash
python3 work/R49-T033/check.py
```
Generates:
- `work/R49-T033/tool_versions.txt`
- `work/R49-T033/inputs.json`
- `work/R49-T033/results.json`
- `work/R49-T033/pipeline_traces.json`
Exits with code `0` on success.
