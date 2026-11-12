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

---

*Master these using MCP with these tools for enhanced productivity and seamless integration.*
## Applied Lab: Client Configuration Validation (R49-T046)

This local Python lab validates a server-launch configuration containing a command, an argument array and explicitly named environment keys. Environment values are redacted in the returned summary.

Run from the repository root:

    python3 12-tooling/applied-labs/r49-t046/example.py

Run the tests:

    python3 -m unittest discover -s 12-tooling/applied-labs/r49-t046 -p "test_*.py" -v

The lab compares a baseline implementation with a refactored implementation that extracts environment redaction into a named function.

[Open the R49-T046 applied lab](applied-labs/r49-t046/README.md)

This is a local simulation. It validates configuration only and does not launch a process or establish a real MCP connection.
