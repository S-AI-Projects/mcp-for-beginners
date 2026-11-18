# R49-T011: Capability Negotiation and Feature Gating

## Purpose & Lesson Connection

In Model Context Protocol (MCP) applications, clients and servers negotiate capabilities during session initialization. This ensures both sides understand which protocol primitives (e.g., `tools`, `prompts`, `resources`, `logging`) are available for the session.

In the **Semantic Search Integration** lab (`11-MCPServerHandsOnLabs/07-Semantic-Search`), the server exposes semantic search functionality primarily via tool invocations (such as `semantic_search_products`). When a client advertises capabilities that the server does not support (or vice versa), the active session capability set is determined by the intersection of both sets. Any subsequent call targeting a capability outside this negotiated set must be gated and rejected before dispatch.

This runnable concept example demonstrates:
1. Intersecting client and server capabilities.
2. Negotiating `{"tools"}` from client `{"tools", "resources"}` and server `{"tools", "prompts"}`.
3. Successfully dispatching operations under the negotiated `tools` capability.
4. Rejecting calls to `resources` before dispatch with a `CapabilityNotNegotiatedError`.

## Prerequisites

- Python 3.8+ (standard library only)
- Local checkout of this repository
- No external Python packages, cloud credentials, GPU, or database connections required.

## Fixtures

```python
# Client capabilities
client_capabilities = {"tools", "resources"}

# Server capabilities
server_capabilities = {"tools", "prompts"}

# Negotiated capability set
negotiated_capabilities = {"tools"}
```

## Running the Example

From the repository root, run:

```bash
python3 11-MCPServerHandsOnLabs/07-Semantic-Search/applied-labs/r49-t011/example.py
```

### Expected Output

```text
=== MCP Capability Negotiation Demo (R49-T011) ===
Client capabilities: ['resources', 'tools']
Server capabilities: ['prompts', 'tools']
Negotiated capabilities: ['tools']

[Action 1] Calling negotiated capability 'tools'...
Dispatch successful! Result: {'tool': 'semantic_search_products', 'status': 'success', 'query': 'comfortable running shoes', 'matches': [{'product_id': 'prod-101', 'product_name': 'Trail Running Shoes', 'similarity_score': 0.89}, {'product_id': 'prod-204', 'product_name': 'Comfort Walkers', 'similarity_score': 0.82}]}

[Action 2] Calling unnegotiated capability 'resources'...
Successfully rejected before dispatch: Capability 'resources' was not negotiated. Negotiated capabilities: ['tools']

Demo completed successfully. No server process or external services contacted.
```

## Validation & Dispatch Rules

- **Intersection**: Negotiated capabilities = `set(client_capabilities) & set(server_capabilities)`.
- **Pre-dispatch Gating**: If a caller attempts to dispatch to a capability not present in `negotiated_capabilities`, a `CapabilityNotNegotiatedError` is raised immediately before any handler execution.
- **Uninitialized Sessions**: Calling `dispatch()` before `negotiate()` raises `RuntimeError`.
- **Type Safety**: Capability collections must be iterables of non-empty strings.

## Running the Unit Tests

From the repository root, run:

```bash
python3 -m unittest discover -s 11-MCPServerHandsOnLabs/07-Semantic-Search/applied-labs/r49-t011 -p "test_*.py"
```

The test suite covers:
- Exact contract negotiation (`{"tools", "resources"}` & `{"tools", "prompts"}` $\rightarrow$ `{"tools"}`)
- Dispatching negotiated tools
- Rejection of unnegotiated resources prior to dispatch
- Calling dispatch before negotiation
- Disjoint capability sets
- Empty capability sets
- Input type validation
- Missing handler handling

## Scope and Limitations

This example is a bounded, local concept demonstration of capability discovery, intersection, and gating. It does not spawn background processes, open network sockets, connect to Azure OpenAI, or interact with PostgreSQL/pgvector.
