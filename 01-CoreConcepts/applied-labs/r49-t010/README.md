
# R49-T010: Capability Negotiation

## Overview

This local simulation demonstrates capability intersection and feature gating between an MCP client and server.

Client capabilities:
- tools
- resources

Server capabilities:
- tools
- prompts

The negotiated capability set is:

`{'tools'}`

Only negotiated capabilities can be invoked.

## Requirements

- Python 3
- Python standard library only
- Local repository checkout

## Run the Example

From the repository root:

```bash
python3 01-CoreConcepts/applied-labs/r49-t010/example.py tools
```

Expected output:

```text
Negotiated capabilities: ['tools']
Result: Mock tool result
Dispatch calls: 1
```

## Applied Questions

### 1. Predict an output

**Question:** What happens when the client invokes `tools`?

**Answer:** The invocation succeeds and returns `Mock tool result`.

**Rationale:** Both client and server advertise `tools`, so it belongs to their intersection.

**Executable check:** `test_tool_invocation`

### 2. Diagnose a failure

**Question:** Why does invoking `resources` fail?

**Answer:** The server does not advertise `resources`, so it is not negotiated.

**Rationale:** A capability advertised by only one participant is excluded from the intersection.

**Executable check:** `test_resources_rejected`

Run:

```bash
python3 01-CoreConcepts/applied-labs/r49-t010/example.py resources
```

Expected output:

```text
Negotiated capabilities: ['tools']
Rejected before dispatch: Capability 'resources' was not negotiated
Dispatch calls: 0
```

The command exits with status 1 intentionally.

### 3. Choose a boundary policy

**Question:** Should unsupported capabilities be forwarded or rejected before dispatch?

**Answer:** Reject them before dispatch.

**Rationale:** The client must not invoke functionality that was not negotiated.

**Executable check:** `test_rejection_happens_before_dispatch`

The dispatch counter must remain zero after rejection.

## Run Tests

```bash
python3 -m unittest discover -s 01-CoreConcepts/applied-labs/r49-t010 -p "test_*.py"
```

## Scope and Limitations

This is a local simulation using fixed capability sets and a mock tool result.

It demonstrates set intersection and pre-dispatch validation.

It does not implement actual MCP initialization, JSON-RPC messages, transport communication, dynamic capability discovery or protocol version negotiation.

It makes no claims about real hardware, cloud services or trained-model performance.
