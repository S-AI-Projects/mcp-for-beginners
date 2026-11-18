"""Read-only environment preflight checker with state trace and invariant verification.

Task R49-T014: Installation preflight report — invariant and state trace.
"""

from typing import Any, Dict, List, Optional, Set, Tuple


class PreflightChecker:
    """Performs deterministic read-only preflight checks and records state transitions."""

    def __init__(
        self,
        required_executables: List[str],
        required_config_fields: List[str],
        secret_fields: Optional[Set[str]] = None,
    ):
        self.required_executables = list(required_executables)
        self.required_config_fields = list(required_config_fields)
        self.secret_fields = set(secret_fields or {"api_key", "token", "secret", "password"})
        self.state_trace: List[Dict[str, Any]] = []

    def run_preflight(
        self,
        available_executables: Set[str],
        config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Run preflight checks recording step-by-step state trace.

        Parameters:
            available_executables: Set of executables present in mock environment.
            config: Local configuration dictionary.

        Returns:
            Preflight report with success flag, failures, redacted config summary, and trace.
        """
        self.state_trace = []
        failures: List[str] = []

        # Step 0: Initial state
        self._record_step(
            stage="initial",
            status="started",
            missing_executables=[],
            missing_config_fields=[],
            current_failures=[],
        )

        # Step 1: Check executables
        missing_executables = [
            exe for exe in self.required_executables if exe not in available_executables
        ]
        for exe in missing_executables:
            failures.append(f"Missing required executable: '{exe}'")

        self._record_step(
            stage="executables_checked",
            status="in_progress",
            missing_executables=missing_executables,
            missing_config_fields=[],
            current_failures=list(failures),
        )

        # Step 2: Check config fields
        missing_config_fields = [
            field for field in self.required_config_fields if field not in config or config[field] is None
        ]
        for field in missing_config_fields:
            failures.append(f"Missing required config field: '{field}'")

        self._record_step(
            stage="config_checked",
            status="in_progress",
            missing_executables=missing_executables,
            missing_config_fields=missing_config_fields,
            current_failures=list(failures),
        )

        # Step 3: Redact config
        redacted_config = {}
        for k, v in config.items():
            if k in self.secret_fields:
                redacted_config[k] = "[REDACTED]"
            else:
                redacted_config[k] = v

        overall_passed = len(failures) == 0

        # Step 4: Final evaluation
        self._record_step(
            stage="completed",
            status="passed" if overall_passed else "failed",
            missing_executables=missing_executables,
            missing_config_fields=missing_config_fields,
            current_failures=list(failures),
        )

        # Invariant check: overall_passed is True iff failures is empty
        invariant_holds = self._verify_invariants(overall_passed, failures)

        return {
            "passed": overall_passed,
            "failures": failures,
            "missing_executables": missing_executables,
            "missing_config_fields": missing_config_fields,
            "redacted_config": redacted_config,
            "state_trace": self.state_trace,
            "invariant_verified": invariant_holds,
        }

    def _record_step(self, stage: str, status: str, **kwargs: Any) -> None:
        """Record an immutable snapshot of the intermediate verification state."""
        self.state_trace.append({
            "step_index": len(self.state_trace),
            "stage": stage,
            "status": status,
            **kwargs,
        })

    def _verify_invariants(self, overall_passed: bool, failures: List[str]) -> bool:
        """Verify that the intermediate state strictly implies the final output."""
        if len(self.state_trace) != 4:
            return False

        step1 = self.state_trace[1]  # executables
        step2 = self.state_trace[2]  # config
        step3 = self.state_trace[3]  # completed

        expected_failures_count = len(step1["missing_executables"]) + len(step2["missing_config_fields"])
        if len(failures) != expected_failures_count:
            return False

        if overall_passed != (expected_failures_count == 0):
            return False

        return True


def main() -> None:
    """Run demonstration with normal, missing executable, and missing config scenarios."""
    print("=== Environment Preflight Report & State Trace (R49-T014) ===")

    checker = PreflightChecker(
        required_executables=["node", "python3"],
        required_config_fields=["server_host", "port", "api_key"],
    )

    # 1. Complete fixture (passes)
    print("\n--- 1. Complete Fixture (Passes) ---")
    res1 = checker.run_preflight(
        available_executables={"node", "python3", "git"},
        config={"server_host": "localhost", "port": 8080, "api_key": "secret-token-12345"},
    )
    print(f"Preflight Passed: {res1['passed']}")
    print(f"Redacted Config: {res1['redacted_config']}")
    print(f"Invariant Verified: {res1['invariant_verified']}")
    print(f"Trace Steps: {len(res1['state_trace'])}")

    # 2. Missing executable fixture
    print("\n--- 2. Missing Executable Fixture ---")
    res2 = checker.run_preflight(
        available_executables={"python3"},
        config={"server_host": "localhost", "port": 8080, "api_key": "secret-token-12345"},
    )
    print(f"Preflight Passed: {res2['passed']}")
    print(f"Actionable Failures: {res2['failures']}")

    # 3. Missing config field fixture
    print("\n--- 3. Missing Config Field Fixture ---")
    res3 = checker.run_preflight(
        available_executables={"node", "python3"},
        config={"server_host": "localhost"},
    )
    print(f"Preflight Passed: {res3['passed']}")
    print(f"Actionable Failures: {res3['failures']}")

    print("\nPreflight demonstration complete. No external services or package installations attempted.")


if __name__ == "__main__":
    main()
