"""Client-consent gate state machine for sampling with equivalence verification.

Task R49-T016: Client-consent gate — refactor the teaching example.
"""

from enum import Enum
from typing import Any, Callable, Dict, Optional, Tuple


class ConsentState(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"


class InvalidStateError(RuntimeError):
    """Raised when an operation is invalid for the current request state."""
    pass


# --- Baseline Monolithic Implementation ---
class BaselineConsentGate:
    """Monolithic baseline: tracks state, enforces policy, and calls model stub."""

    def __init__(self, model_stub: Optional[Callable[[str], str]] = None):
        self.state = ConsentState.PENDING
        self.response: Optional[str] = None
        self.model_calls = 0
        self._model_stub = model_stub or (lambda prompt: f"Echo: {prompt}")

    def decide(self, approved: bool, prompt: str) -> Dict[str, Any]:
        """Process consent decision and invoke model if approved."""
        if self.state != ConsentState.PENDING:
            raise InvalidStateError(f"Request is already resolved as '{self.state.value}' and cannot be updated")

        if approved:
            self.state = ConsentState.APPROVED
            self.model_calls += 1
            self.response = self._model_stub(prompt)
        else:
            self.state = ConsentState.DENIED
            self.response = None

        return {
            "state": self.state.value,
            "response": self.response,
            "model_calls": self.model_calls,
        }


# --- Refactored Implementation (Extracted Named Responsibility: StatePolicy) ---
class ConsentStateMachine:
    """Extracted named responsibility: Manages state transitions and guards immutability."""

    def __init__(self):
        self.state = ConsentState.PENDING

    def transition(self, approved: bool) -> ConsentState:
        """Validate and transition from pending to approved or denied."""
        if self.state != ConsentState.PENDING:
            raise InvalidStateError(
                f"Request is already resolved as '{self.state.value}' and cannot be updated"
            )
        self.state = ConsentState.APPROVED if approved else ConsentState.DENIED
        return self.state


class RefactoredConsentGate:
    """Refactored gate: delegates state transitions to ConsentStateMachine and dispatches model."""

    def __init__(self, model_stub: Optional[Callable[[str], str]] = None):
        self.state_machine = ConsentStateMachine()
        self.response: Optional[str] = None
        self.model_calls = 0
        self._model_stub = model_stub or (lambda prompt: f"Echo: {prompt}")

    @property
    def state(self) -> ConsentState:
        return self.state_machine.state

    def decide(self, approved: bool, prompt: str) -> Dict[str, Any]:
        """Delegate transition and execute model call only when approved."""
        new_state = self.state_machine.transition(approved)

        if new_state == ConsentState.APPROVED:
            self.model_calls += 1
            self.response = self._model_stub(prompt)
        else:
            self.response = None

        return {
            "state": self.state.value,
            "response": self.response,
            "model_calls": self.model_calls,
        }


def run_equivalence_check(prompt: str = "Generate summary") -> Tuple[bool, Dict[str, Any]]:
    """Prove before/after equivalence between baseline and refactored gates on fixtures."""
    # Test Approved Scenario
    base_app = BaselineConsentGate()
    ref_app = RefactoredConsentGate()
    res_base_app = base_app.decide(approved=True, prompt=prompt)
    res_ref_app = ref_app.decide(approved=True, prompt=prompt)

    # Test Denied Scenario
    base_den = BaselineConsentGate()
    ref_den = RefactoredConsentGate()
    res_base_den = base_den.decide(approved=False, prompt=prompt)
    res_ref_den = ref_den.decide(approved=False, prompt=prompt)

    # Test Completed Re-approval Rejection
    def check_reapproval(gate):
        try:
            gate.decide(approved=True, prompt=prompt)
            return False
        except InvalidStateError:
            return True

    reapp_base_app = check_reapproval(base_app)
    reapp_ref_app = check_reapproval(ref_app)

    equivalent = (
        res_base_app == res_ref_app
        and res_base_den == res_ref_den
        and reapp_base_app == reapp_ref_app == True
    )

    return equivalent, {
        "approved_result": res_ref_app,
        "denied_result": res_ref_den,
        "reapproval_rejected": reapp_ref_app,
    }


def main() -> None:
    """Run demonstration showing sampling consent gate behavior and equivalence."""
    print("=== Client-Consent Gate State Machine (R49-T016) ===")

    is_equiv, summary = run_equivalence_check("Generate product description")
    print(f"Equivalence between Baseline and Refactored Gate: {is_equiv}")
    print(f"Approved Execution Result: {summary['approved_result']}")
    print(f"Denied Execution Result: {summary['denied_result']}")
    print(f"Re-approval Blocked for Completed Request: {summary['reapproval_rejected']}")

    print("\nDemo completed. Denied consent made 0 model calls; approved consent made 1 call.")


if __name__ == "__main__":
    main()
