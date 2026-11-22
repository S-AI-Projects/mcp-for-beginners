"""
Simple Auth: Injected Token Verifier, Identity Differentiation & State Invariant Pipeline.

Lesson Extension: 03-GettingStarted/11-simple-auth
Task ID: R49-T033

Key Requirements:
- Validate a local bearer-token fixture through an injected verifier.
- Distinguish three identity outcomes:
    1. Missing token -> unauthenticated
    2. Unknown token -> invalid
    3. Known token -> subject
- Zero token exposure: No raw token value ever appears in logs or public state traces.
- Focus: Record intermediate state after each step and verify the invariant linking
  that state to the final output.
"""

from dataclasses import dataclass, field
from enum import Enum
import hashlib
import json
import re
from typing import Any, Dict, List, Optional, Protocol, Tuple


# Local Deterministic Token Fixture (Zero external providers)
LOCAL_TOKEN_FIXTURE: Dict[str, Dict[str, Any]] = {
    "bearer-alice-token-991": {
        "sub": "alice_andhare",
        "roles": ["admin", "analyst"],
        "scope": "retail:read"
    },
    "bearer-bob-token-882": {
        "sub": "bob_retail",
        "roles": ["analyst"],
        "scope": "retail:read"
    }
}


class AuthStatus(str, Enum):
    UNAUTHENTICATED = "unauthenticated"
    INVALID = "invalid"
    AUTHENTICATED = "authenticated"


class AuditLogger:
    """Audit logger with automatic token value sanitization."""

    def __init__(self):
        self.records: List[Dict[str, Any]] = []

    def _sanitize(self, message: str) -> str:
        # Redact Bearer tokens
        sanitized = re.sub(r"(?i)bearer\s+[A-Za-z0-9_\-\.]+", "Bearer [REDACTED]", message)
        # Redact any raw fixture tokens explicitly if passed directly
        for raw_token in LOCAL_TOKEN_FIXTURE.keys():
            sanitized = sanitized.replace(raw_token, "[REDACTED]")
        return sanitized

    def log(self, level: str, event: str, message: str, **kwargs):
        sanitized_msg = self._sanitize(message)
        sanitized_kwargs = {}
        for k, v in kwargs.items():
            if isinstance(v, str):
                sanitized_kwargs[k] = self._sanitize(v)
            else:
                sanitized_kwargs[k] = v

        self.records.append({
            "level": level,
            "event": event,
            "message": sanitized_msg,
            "metadata": sanitized_kwargs
        })

    def contains_raw_token(self, raw_token: str) -> bool:
        """Scan all stored log records for raw token leaks."""
        if not raw_token:
            return False
        dumped = json.dumps(self.records)
        return raw_token in dumped


class TokenVerifierProtocol(Protocol):
    """Protocol for injected token verifier."""
    def verify(self, token: str) -> Optional[Dict[str, Any]]:
        ...


class InjectedLocalVerifier:
    """
    Injected Token Verifier backed by local deterministic fixture.
    Can be replaced or mocked without modifying pipeline logic.
    """

    def __init__(self, token_store: Optional[Dict[str, Dict[str, Any]]] = None):
        self._tokens = token_store if token_store is not None else dict(LOCAL_TOKEN_FIXTURE)
        self.verification_call_count = 0

    def verify(self, token: str) -> Optional[Dict[str, Any]]:
        self.verification_call_count += 1
        return self._tokens.get(token)


# ------------------------------------------------------------------------------
# Intermediate Pipeline State Data Structures
# ------------------------------------------------------------------------------

@dataclass
class ExtractionState:
    """Step 1 Intermediate State: Token extraction from headers."""
    has_auth_header: bool
    is_bearer_format: bool
    token_extracted: bool
    token_fingerprint: Optional[str] = None  # Non-reversible SHA-256 prefix for trace safety


@dataclass
class VerificationState:
    """Step 2 Intermediate State: Verifier execution outcome."""
    verifier_invoked: bool
    token_recognized: bool
    claims_present: bool
    claims_subject: Optional[str] = None
    error_code: Optional[str] = None


@dataclass
class ResolutionState:
    """Step 3 Intermediate State: Final identity decision."""
    final_status: AuthStatus
    resolved_subject: Optional[str]
    error_message: Optional[str]


@dataclass
class PipelineExecutionTrace:
    """Full execution trace recording state snapshots after every pipeline step."""
    step_1_extraction: ExtractionState
    step_2_verification: VerificationState
    step_3_resolution: ResolutionState
    sanitized_logs: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "step_1_extraction": {
                "has_auth_header": self.step_1_extraction.has_auth_header,
                "is_bearer_format": self.step_1_extraction.is_bearer_format,
                "token_extracted": self.step_1_extraction.token_extracted,
                "token_fingerprint": self.step_1_extraction.token_fingerprint,
            },
            "step_2_verification": {
                "verifier_invoked": self.step_2_verification.verifier_invoked,
                "token_recognized": self.step_2_verification.token_recognized,
                "claims_present": self.step_2_verification.claims_present,
                "claims_subject": self.step_2_verification.claims_subject,
                "error_code": self.step_2_verification.error_code,
            },
            "step_3_resolution": {
                "final_status": self.step_3_resolution.final_status.value,
                "resolved_subject": self.step_3_resolution.resolved_subject,
                "error_message": self.step_3_resolution.error_message,
            },
            "log_records_count": len(self.sanitized_logs),
        }


# ------------------------------------------------------------------------------
# Authentication Pipeline Implementation
# ------------------------------------------------------------------------------

class SimpleAuthPipeline:
    """
    Three-stage authentication pipeline with state tracking and injected verifier.
    """

    def __init__(self, verifier: InjectedLocalVerifier, logger: Optional[AuditLogger] = None):
        self.verifier = verifier
        self.logger = logger or AuditLogger()

    def authenticate_request(self, headers: Optional[Dict[str, str]]) -> PipelineExecutionTrace:
        headers = headers or {}
        auth_header = headers.get("Authorization") or headers.get("authorization")

        # ----------------------------------------------------------------------
        # STEP 1: Extraction
        # ----------------------------------------------------------------------
        has_auth_header = auth_header is not None
        is_bearer_format = False
        raw_token: Optional[str] = None
        token_fingerprint: Optional[str] = None

        if has_auth_header and isinstance(auth_header, str):
            parts = auth_header.strip().split(None, 1)
            if len(parts) == 2 and parts[0].lower() == "bearer" and parts[1].strip():
                is_bearer_format = True
                raw_token = parts[1].strip()
                # Compute irreversible fingerprint for trace
                token_fingerprint = hashlib.sha256(raw_token.encode()).hexdigest()[:8]

        extraction_state = ExtractionState(
            has_auth_header=has_auth_header,
            is_bearer_format=is_bearer_format,
            token_extracted=raw_token is not None,
            token_fingerprint=token_fingerprint
        )

        if not extraction_state.token_extracted:
            self.logger.log("INFO", "AUTH_EXTRACTION_FAILED", "No valid bearer token present in request headers.")
        else:
            self.logger.log(
                "INFO",
                "AUTH_TOKEN_EXTRACTED",
                "Bearer token extracted successfully.",
                fingerprint=token_fingerprint
            )

        # ----------------------------------------------------------------------
        # STEP 2: Injected Verification
        # ----------------------------------------------------------------------
        if not extraction_state.token_extracted:
            verification_state = VerificationState(
                verifier_invoked=False,
                token_recognized=False,
                claims_present=False,
                error_code="TOKEN_MISSING"
            )
        else:
            claims = self.verifier.verify(raw_token)
            if claims is not None:
                verification_state = VerificationState(
                    verifier_invoked=True,
                    token_recognized=True,
                    claims_present=True,
                    claims_subject=claims.get("sub"),
                    error_code=None
                )
                self.logger.log("INFO", "VERIFICATION_SUCCESS", f"Token verified for subject: {claims.get('sub')}")
            else:
                verification_state = VerificationState(
                    verifier_invoked=True,
                    token_recognized=False,
                    claims_present=False,
                    error_code="TOKEN_UNRECOGNIZED"
                )
                self.logger.log("WARN", "VERIFICATION_FAILED", "Injected verifier rejected bearer token: unknown credential.")

        # ----------------------------------------------------------------------
        # STEP 3: Identity Resolution
        # ----------------------------------------------------------------------
        if not extraction_state.token_extracted:
            # Missing token -> unauthenticated
            final_status = AuthStatus.UNAUTHENTICATED
            resolved_subject = None
            error_message = "Missing bearer token in Authorization header."
        elif not verification_state.token_recognized:
            # Unknown token -> invalid
            final_status = AuthStatus.INVALID
            resolved_subject = None
            error_message = "Invalid or unrecognized bearer token."
        else:
            # Known token -> subject
            final_status = AuthStatus.AUTHENTICATED
            resolved_subject = verification_state.claims_subject
            error_message = None

        resolution_state = ResolutionState(
            final_status=final_status,
            resolved_subject=resolved_subject,
            error_message=error_message
        )

        return PipelineExecutionTrace(
            step_1_extraction=extraction_state,
            step_2_verification=verification_state,
            step_3_resolution=resolution_state,
            sanitized_logs=list(self.logger.records)
        )


# ------------------------------------------------------------------------------
# Invariant Verification Engine
# ------------------------------------------------------------------------------

def test_pipeline_invariants(trace: PipelineExecutionTrace) -> Dict[str, bool]:
    """
    Test the fundamental invariants linking intermediate states to the final output:
    1. INVARIANT_MISSING: (no token) <=> (status == UNAUTHENTICATED and subject is None)
    2. INVARIANT_INVALID: (token present and not recognized) <=> (status == INVALID and subject is None)
    3. INVARIANT_VALID: (token present and recognized) <=> (status == AUTHENTICATED and subject == claims_sub)
    4. INVARIANT_ZERO_TOKEN_LOGS: No log record contains raw tokens or unredacted bearer secrets
    """
    ext = trace.step_1_extraction
    ver = trace.step_2_verification
    res = trace.step_3_resolution

    # Invariant 1: Missing Token
    condition_missing = not ext.token_extracted
    outcome_missing = (res.final_status == AuthStatus.UNAUTHENTICATED and res.resolved_subject is None)
    inv_missing = (condition_missing == outcome_missing)

    # Invariant 2: Invalid/Unknown Token
    condition_invalid = ext.token_extracted and not ver.token_recognized
    outcome_invalid = (res.final_status == AuthStatus.INVALID and res.resolved_subject is None)
    inv_invalid = (condition_invalid == outcome_invalid)

    # Invariant 3: Valid/Known Token
    condition_valid = ext.token_extracted and ver.token_recognized
    outcome_valid = (
        res.final_status == AuthStatus.AUTHENTICATED
        and res.resolved_subject is not None
        and res.resolved_subject == ver.claims_subject
    )
    inv_valid = (condition_valid == outcome_valid)

    # Invariant 4: No log leak
    dumped_logs = json.dumps(trace.sanitized_logs)
    no_raw_tokens_in_logs = not any(token in dumped_logs for token in LOCAL_TOKEN_FIXTURE.keys())

    return {
        "invariant_missing_token": inv_missing,
        "invariant_invalid_token": inv_invalid,
        "invariant_valid_token": inv_valid,
        "invariant_logs_redacted": no_raw_tokens_in_logs,
        "all_invariants_hold": inv_missing and inv_invalid and inv_valid and no_raw_tokens_in_logs
    }


def run_demonstration() -> Dict[str, Any]:
    """Run full demonstration across missing, invalid, and valid tokens."""
    print("=" * 75)
    print("Simple Auth: Injected Verifier, Identity Differentiation & Invariants (R49-T033)")
    print("=" * 75)

    logger = AuditLogger()
    verifier = InjectedLocalVerifier()
    pipeline = SimpleAuthPipeline(verifier=verifier, logger=logger)

    scenarios = [
        ("Missing Token", {}),
        ("Invalid / Unknown Token", {"Authorization": "Bearer unknown-bogus-token-xyz"}),
        ("Valid Known Token (Alice)", {"Authorization": "Bearer bearer-alice-token-991"}),
        ("Valid Known Token (Bob)", {"Authorization": "Bearer bearer-bob-token-882"}),
    ]

    demo_results = []
    for name, headers in scenarios:
        trace = pipeline.authenticate_request(headers)
        invariants = test_pipeline_invariants(trace)

        print(f"\n[Scenario: {name}]")
        print(f"  Step 1 Extraction   : token_extracted={trace.step_1_extraction.token_extracted}, fingerprint={trace.step_1_extraction.token_fingerprint}")
        print(f"  Step 2 Verification : invoked={trace.step_2_verification.verifier_invoked}, recognized={trace.step_2_verification.token_recognized}, claims_sub={trace.step_2_verification.claims_subject}")
        print(f"  Step 3 Resolution   : status={trace.step_3_resolution.final_status.value}, subject={trace.step_3_resolution.resolved_subject}")
        print(f"  Invariants Hold     : {invariants['all_invariants_hold']}")

        demo_results.append({
            "scenario": name,
            "status": trace.step_3_resolution.final_status.value,
            "subject": trace.step_3_resolution.resolved_subject,
            "invariants_hold": invariants["all_invariants_hold"]
        })

    # Log leak audit check
    print("\n" + "-" * 75)
    print("[Log Redaction Audit]")
    leaks = [t for t in LOCAL_TOKEN_FIXTURE.keys() if logger.contains_raw_token(t)]
    print(f"  Total log entries recorded : {len(logger.records)}")
    print(f"  Raw token leaks detected   : {len(leaks)} (Expected: 0)")
    assert len(leaks) == 0, f"SECURITY LEAK: Found unredacted tokens in logs: {leaks}"

    print("=" * 75)
    print("All auth scenarios and invariant checks completed successfully.")
    print("=" * 75)

    return {"scenarios": demo_results, "leak_free": len(leaks) == 0}


if __name__ == "__main__":
    run_demonstration()
