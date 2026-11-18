"""Read-only environment preflight checker with offline service adapter.

Task R49-T015: Installation preflight report — offline service adapter.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Set


class EnvironmentAdapter(ABC):
    """Abstract interface for inspecting environment state without direct system coupling."""

    @abstractmethod
    def check_executable(self, name: str) -> bool:
        """Return True if executable is present."""
        pass

    @abstractmethod
    def get_config_value(self, key: str) -> Optional[str]:
        """Return configuration string or None if absent."""
        pass


class LocalOfflineAdapter(EnvironmentAdapter):
    """Deterministic local mock adapter decoupled from live OS or network calls."""

    def __init__(
        self,
        available_executables: Set[str],
        config_store: Dict[str, str],
    ):
        self._executables = set(available_executables)
        self._config = dict(config_store)

    def check_executable(self, name: str) -> bool:
        return name in self._executables

    def get_config_value(self, key: str) -> Optional[str]:
        return self._config.get(key)


def run_preflight_precheck(
    adapter: EnvironmentAdapter,
    required_executables: List[str],
    required_config_fields: List[str],
    secret_fields: Optional[Set[str]] = None,
) -> Dict[str, Any]:
    """Execute preflight check using the provided environment adapter.

    Parameters:
        adapter: An EnvironmentAdapter instance providing executable and config checks.
        required_executables: List of required executable names.
        required_config_fields: List of required configuration field keys.
        secret_fields: Set of field names whose values must be redacted.

    Returns:
        Dict containing success flag, actionable failure lists, and redacted configuration.
    """
    secrets = set(secret_fields or {"api_key", "secret", "token", "password"})
    failures: List[str] = []
    missing_executables: List[str] = []
    missing_config_fields: List[str] = []
    redacted_config: Dict[str, str] = {}

    # Check required executables
    for exe in required_executables:
        if not adapter.check_executable(exe):
            missing_executables.append(exe)
            failures.append(f"Executable missing: '{exe}'")

    # Check required config fields and redact secrets
    for field in required_config_fields:
        val = adapter.get_config_value(field)
        if val is None or not str(val).strip():
            missing_config_fields.append(field)
            failures.append(f"Config field missing or empty: '{field}'")
        else:
            if field in secrets:
                redacted_config[field] = "[REDACTED]"
            else:
                redacted_config[field] = str(val)

    passed = len(failures) == 0

    return {
        "passed": passed,
        "failures": failures,
        "missing_executables": missing_executables,
        "missing_config_fields": missing_config_fields,
        "redacted_config": redacted_config,
    }


def main() -> None:
    """Run demonstration with complete and failing fixtures."""
    print("=== Environment Preflight with Offline Adapter (R49-T015) ===")

    req_executables = ["node", "python3"]
    req_config = ["database_url", "api_key", "port"]

    # 1. Complete fixture (passes)
    complete_adapter = LocalOfflineAdapter(
        available_executables={"node", "python3", "docker"},
        config_store={
            "database_url": "postgresql://localhost:5432/mcp",
            "api_key": "top_secret_prod_key",
            "port": "8080",
        },
    )
    result_complete = run_preflight_precheck(complete_adapter, req_executables, req_config)
    print("\n--- Complete Fixture ---")
    print(f"Preflight Passed: {result_complete['passed']}")
    print(f"Redacted Config: {result_complete['redacted_config']}")

    # 2. Missing executable fixture
    missing_exe_adapter = LocalOfflineAdapter(
        available_executables={"python3"},
        config_store={"database_url": "postgresql://localhost", "api_key": "k", "port": "8080"},
    )
    result_exe = run_preflight_precheck(missing_exe_adapter, req_executables, req_config)
    print("\n--- Missing Executable Fixture ---")
    print(f"Preflight Passed: {result_exe['passed']}")
    print(f"Actionable Failures: {result_exe['failures']}")

    # 3. Missing config fixture
    missing_config_adapter = LocalOfflineAdapter(
        available_executables={"node", "python3"},
        config_store={"database_url": "postgresql://localhost"},
    )
    result_cfg = run_preflight_precheck(missing_config_adapter, req_executables, req_config)
    print("\n--- Missing Config Fixture ---")
    print(f"Preflight Passed: {result_cfg['passed']}")
    print(f"Actionable Failures: {result_cfg['failures']}")

    print("\nDemo complete. Adapter operated completely offline without touching the OS.")


if __name__ == "__main__":
    main()
