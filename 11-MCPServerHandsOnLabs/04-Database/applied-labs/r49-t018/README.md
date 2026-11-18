# R49-T018: Capability Negotiation — Failure and Recovery Example

## Purpose & Lesson Connection

In "Database Design and Schema" (`11-MCPServerHandsOnLabs/04-Database`), multi-tenant database systems require strict session boundaries and capability gating. When connecting an MCP client to a database server:
1. Client and server capabilities are intersected during the initialize handshake (e.g. client `{tools, resources}` and server `{tools, prompts}` negotiate `{tools}`).
2. Requests for unnegotiated capabilities (such as direct `resources` schema reads) must be rejected prior to dispatch.
3. When tool executions encounter missing or invalid parameters (e.g. omitted multi-tenant `store_id`), the server reports a clear actionable error, while preserving session health and demonstrating immediate recovery on subsequent valid inputs.

## Running the Example

From the repository root:

```bash
python3 11-MCPServerHandsOnLabs/04-Database/applied-labs/r49-t018/example.py
```

### Expected Output

```text
=== Database Capability Negotiation & Recovery Demo (R49-T018) ===
Client capabilities: ['resources', 'tools']
Server capabilities: ['prompts', 'tools']
Negotiated capabilities: ['tools']

[Step 1] Attempting to invoke unnegotiated capability 'resources'...
Successfully rejected before dispatch: Capability 'resources' was not negotiated. Negotiated capabilities: ['tools']

[Step 2] Executing query with missing 'store_id'...
Caught documented missing-data error: Missing required parameter: 'store_id' is mandatory for multi-tenant isolation

[Step 3] Recovering on next valid input (supplying store_id)...
Recovery successful! Retrieved 2 rows for store store-east-01.

Demo completed successfully. No live PostgreSQL instance or network required.
```

## Running the Unit Tests

```bash
python3 -m unittest discover -s 11-MCPServerHandsOnLabs/04-Database/applied-labs/r49-t018 -p "test_*.py"
```

## Scope and Limitations

This is a local mock simulation of database capability negotiation and failure recovery. It does not connect to live PostgreSQL instances, provision tables, or require network access.
