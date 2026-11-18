# R49-T015: Installation Preflight Report — Offline Service Adapter

## Purpose & Lesson Connection

In "Practical Implementation" (`04-PracticalImplementation`), preflight checks protect systems against missing dependencies and misconfigurations. To decouple testing and verification from host environmental state, external discovery and configuration reading must be placed behind an explicit callable interface (`EnvironmentAdapter`).

This applied lab demonstrates:
1. An abstract interface `EnvironmentAdapter` defining `check_executable` and `get_config_value`.
2. A deterministic `LocalOfflineAdapter` that evaluates fixtures without system calls or external network dependencies.
3. Separate actionable error messages for missing executables vs. missing configuration fields.
4. Redaction of sensitive values (such as API keys and passwords).

## Offline Adapter vs. Real-Service Behaviors

While `LocalOfflineAdapter` guarantees deterministic and safe testing, it explicitly **does not establish** the following real-world behaviors:
1. **Binary Architecture & Execution Rights**: Does not verify CPU architecture compatibility (e.g. `arm64` vs. `x86_64`) or POSIX file execution permissions (`+x`).
2. **Version Semantics**: Does not parse `--version` output to ensure executables meet semantic version constraints.
3. **Network Connectivity**: Does not attempt socket connections or DNS resolution for configured hosts or endpoints.
4. **Credential Validity**: Does not authenticate tokens or keys against live identity providers or databases.

## Running the Example

From the repository root:

```bash
python3 04-PracticalImplementation/applied-labs/r49-t015/example.py
```

### Expected Output

```text
=== Environment Preflight with Offline Adapter (R49-T015) ===

--- Complete Fixture ---
Preflight Passed: True
Redacted Config: {'database_url': 'postgresql://localhost:5432/mcp', 'api_key': '[REDACTED]', 'port': '8080'}

--- Missing Executable Fixture ---
Preflight Passed: False
Actionable Failures: ["Executable missing: 'node'"]

--- Missing Config Fixture ---
Preflight Passed: False
Actionable Failures: ["Config field missing or empty: 'api_key'", "Config field missing or empty: 'port'"]

Demo complete. Adapter operated completely offline without touching the OS.
```

## Running the Unit Tests

```bash
python3 -m unittest discover -s 04-PracticalImplementation/applied-labs/r49-t015 -p "test_*.py"
```

## Scope and Limitations

This is a local mock simulation running entirely in memory through an adapter interface. No actual binaries are queried, and no network traffic is generated.
