"""
Unit tests for Simple Auth: Injected Verifier, State Invariants & Log Redaction.

Lesson Extension: 03-GettingStarted/11-simple-auth
Task ID: R49-T033

Validates:
- Missing token -> unauthenticated
- Unknown token -> invalid
- Known token -> subject
- Zero token value leakage in logs
- State invariants linking extraction/verification to final resolution
- Deliberate wrong result detection
"""

import os
import sys
import unittest

# Ensure current directory is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from example import (
    SimpleAuthPipeline,
    InjectedLocalVerifier,
    AuditLogger,
    AuthStatus,
    ExtractionState,
    VerificationState,
    ResolutionState,
    PipelineExecutionTrace,
    test_pipeline_invariants,
    LOCAL_TOKEN_FIXTURE,
)


class TestSimpleAuthPipeline(unittest.TestCase):
    """Test suite for injected bearer-token verification and state invariants."""

    def setUp(self):
        self.logger = AuditLogger()
        self.verifier = InjectedLocalVerifier()
        self.pipeline = SimpleAuthPipeline(verifier=self.verifier, logger=self.logger)

    def test_missing_token_unauthenticated(self):
        """
        Missing token scenario:
        - Step 1: token_extracted is False
        - Step 2: verifier is NOT invoked
        - Step 3: status is UNAUTHENTICATED, subject is None
        - Invariants hold
        """
        trace = self.pipeline.authenticate_request({})
        self.assertFalse(trace.step_1_extraction.token_extracted)
        self.assertFalse(trace.step_2_verification.verifier_invoked)
        self.assertEqual(trace.step_3_resolution.final_status, AuthStatus.UNAUTHENTICATED)
        self.assertIsNone(trace.step_3_resolution.resolved_subject)

        invariants = test_pipeline_invariants(trace)
        self.assertTrue(invariants["all_invariants_hold"])
        self.assertTrue(invariants["invariant_missing_token"])

    def test_unknown_token_invalid(self):
        """
        Unknown token scenario:
        - Step 1: token_extracted is True
        - Step 2: verifier invoked, token_recognized is False
        - Step 3: status is INVALID, subject is None
        - Invariants hold
        """
        unknown_token = "bearer-unknown-rogue-secret-777"
        headers = {"Authorization": f"Bearer {unknown_token}"}
        trace = self.pipeline.authenticate_request(headers)

        self.assertTrue(trace.step_1_extraction.token_extracted)
        self.assertTrue(trace.step_2_verification.verifier_invoked)
        self.assertFalse(trace.step_2_verification.token_recognized)
        self.assertEqual(trace.step_3_resolution.final_status, AuthStatus.INVALID)
        self.assertIsNone(trace.step_3_resolution.resolved_subject)

        invariants = test_pipeline_invariants(trace)
        self.assertTrue(invariants["all_invariants_hold"])
        self.assertTrue(invariants["invariant_invalid_token"])

    def test_known_token_subject(self):
        """
        Known token scenario:
        - Step 1: token_extracted is True
        - Step 2: verifier invoked, token_recognized is True, claims match fixture
        - Step 3: status is AUTHENTICATED, subject matches 'alice_andhare'
        - Invariants hold
        """
        valid_token = "bearer-alice-token-991"
        headers = {"Authorization": f"Bearer {valid_token}"}
        trace = self.pipeline.authenticate_request(headers)

        self.assertTrue(trace.step_1_extraction.token_extracted)
        self.assertTrue(trace.step_2_verification.verifier_invoked)
        self.assertTrue(trace.step_2_verification.token_recognized)
        self.assertEqual(trace.step_2_verification.claims_subject, "alice_andhare")
        self.assertEqual(trace.step_3_resolution.final_status, AuthStatus.AUTHENTICATED)
        self.assertEqual(trace.step_3_resolution.resolved_subject, "alice_andhare")

        invariants = test_pipeline_invariants(trace)
        self.assertTrue(invariants["all_invariants_hold"])
        self.assertTrue(invariants["invariant_valid_token"])

    def test_no_token_value_in_logs(self):
        """
        Security invariant: No raw token string must ever appear in logs.
        Scans all logs produced during valid, invalid, and missing token runs.
        """
        tokens_to_test = [
            "bearer-alice-token-991",
            "bearer-bob-token-882",
            "bearer-unknown-rogue-secret-777"
        ]
        for token in tokens_to_test:
            self.pipeline.authenticate_request({"Authorization": f"Bearer {token}"})

        # Also test with missing token
        self.pipeline.authenticate_request({})

        # Verify no token leaks
        for token in tokens_to_test:
            self.assertFalse(
                self.logger.contains_raw_token(token),
                f"SECURITY VIOLATION: Raw token '{token}' leaked into logs!"
            )

    def test_injected_verifier_custom_mock(self):
        """
        Demonstrate verifier injection:
        Injecting a custom verifier allows dynamic credential mocking without altering pipeline.
        """
        custom_verifier = InjectedLocalVerifier(token_store={
            "custom-test-token-42": {"sub": "custom_tester", "roles": ["qa"]}
        })
        custom_pipeline = SimpleAuthPipeline(verifier=custom_verifier)

        # Standard token is now unknown
        t1 = custom_pipeline.authenticate_request({"Authorization": "Bearer bearer-alice-token-991"})
        self.assertEqual(t1.step_3_resolution.final_status, AuthStatus.INVALID)

        # Custom token is recognized
        t2 = custom_pipeline.authenticate_request({"Authorization": "Bearer custom-test-token-42"})
        self.assertEqual(t2.step_3_resolution.final_status, AuthStatus.AUTHENTICATED)
        self.assertEqual(t2.step_3_resolution.resolved_subject, "custom_tester")

    def test_deliberate_wrong_result_makes_test_fail(self):
        """
        Done-when requirement:
        'The contribution focus is demonstrated, and a deliberate wrong result makes the test fail.'

        Simulates a compromised/corrupted pipeline resolution (e.g., granting authenticated
        status despite missing token, or mismatched subject). Proves invariant assertions detect it.
        """
        # Create a corrupted trace where extraction is missing, but resolution claims authenticated
        corrupted_trace = PipelineExecutionTrace(
            step_1_extraction=ExtractionState(
                has_auth_header=False,
                is_bearer_format=False,
                token_extracted=False
            ),
            step_2_verification=VerificationState(
                verifier_invoked=False,
                token_recognized=False,
                claims_present=False
            ),
            step_3_resolution=ResolutionState(
                final_status=AuthStatus.AUTHENTICATED,  # Corrupted!
                resolved_subject="impostor_user",
                error_message=None
            )
        )

        invariants = test_pipeline_invariants(corrupted_trace)
        # Confirm that invariant checks strictly flag the violation
        self.assertFalse(invariants["all_invariants_hold"])
        self.assertFalse(invariants["invariant_missing_token"])

    def test_malformed_authorization_headers(self):
        """Malformed or non-bearer Authorization headers result in UNAUTHENTICATED."""
        malformed_cases = [
            {"Authorization": "Basic dXNlcjpwYXNz"},  # Basic auth, not Bearer
            {"Authorization": "Bearer"},               # Missing token payload
            {"Authorization": "Bearer   "},            # Whitespace token
            {"Authorization": ""},                     # Empty header
            {"OtherHeader": "Bearer some-token"},       # Wrong header name
        ]
        for headers in malformed_cases:
            trace = self.pipeline.authenticate_request(headers)
            self.assertEqual(
                trace.step_3_resolution.final_status,
                AuthStatus.UNAUTHENTICATED,
                f"Failed on header: {headers}"
            )
            self.assertIsNone(trace.step_3_resolution.resolved_subject)


if __name__ == "__main__":
    unittest.main()
