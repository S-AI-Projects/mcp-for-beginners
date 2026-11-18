# 🚀 MCP Tooling

## 🧠 Overview of the MCP Database Integration Learning Path

Here you will learn how to use tools that uses MCP. Your experience using these tools will improve as you connect MCP servers to them.

## 🔗 Official MCP Resources

- 📘 [MCP Documentation](https://modelcontextprotocol.io/) – Detailed tutorials and user guides
- 📜 [MCP Specification (2026-07-28)](https://modelcontextprotocol.io/specification/2026-07-28/) – Protocol architecture and technical references
- 🧑‍💻 [MCP GitHub Repository](https://github.com/modelcontextprotocol) – Open-source SDKs, tools, and code samples
- 🌐 [MCP Community](https://github.com/orgs/modelcontextprotocol/discussions) – Join discussions and contribute to the community
- 🔒 [OWASP MCP Top 10](https://microsoft.github.io/mcp-azure-security-guide/mcp/) – Security best practices and risk mitigations



## 🌟 Community and Support

### Get Help

- **Azure AI Discord**: [Join for expert support](https://discord.com/invite/ByRwuEEgH4)
- **MCP Community**: [Join broader MCP discussions](https://github.com/orgs/modelcontextprotocol/discussions)

## 🚀 Ready to Start?

Begin your journey with **[GitHub Copilot app](./01-copilot-app/README.md)**

## Applied Lab: Client-Configuration Validation — Compare Two Approaches (R49-T013)

When developing MCP tooling, validating client launch configurations is critical for reliability. This applied lab validates command and argument structures, redacts sensitive environment values, and compares direct validation against an independent declarative reference table.

### Run the example

Prerequisite: Python 3 standard library.

From the repository root:

```bash
python3 12-tooling/applied-labs/r49-t013/example.py
```

Expected output:

```text
=== MCP Tooling: Client-Configuration Validation (R49-T013) ===
Case [valid_standard]: AGREED (success=True)
   Redacted Output: {'command': 'python', 'args': ['server.py', '--debug'], 'environment_keys': ['ENV', 'SECRET_KEY']}
Case [valid_minimal]: AGREED (success=True)
   Redacted Output: {'command': 'node', 'args': [], 'environment_keys': []}
Case [invalid_missing_command]: AGREED (success=False)
Case [invalid_single_string_args]: AGREED (success=False)

All cases compared with identical inputs. Secret values were completely redacted.
No child processes were launched.
```

Run the tests with:

```bash
python3 -m unittest discover -s 12-tooling/applied-labs/r49-t013 -p "test_*.py"
```

For complete benchmarking details and documentation, see the [R49-T013 applied lab](./applied-labs/r49-t013/README.md).

**Scope:** This is a local mock simulation comparing validation methods. No server processes or external tools are launched.

---

*Master these using MCP with these tools for enhanced productivity and seamless integration.*