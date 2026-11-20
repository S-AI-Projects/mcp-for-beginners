
# R49-T001: Client-Consent Gate

## Overview

This example demonstrates a local client-consent gate for model sampling requests.

The request starts in the `pending` state. The client can approve or deny the request.

- Approved: The mock model is called exactly once.
- Denied: The mock model is never called.
- Completed requests cannot receive another decision.

## Requirements

- Python 3
- No external packages required.

## Run the Example

From the repository root, execute:

```bash
python3 03-GettingStarted/14-sampling/applied-labs/r49-t001/example.py
```

## Example Inputs and Expected Outputs

### Approved

Input:

```text
approved
```

Expected output:

```text
Final state: approved
Model calls: 1
Result: Mock model response
```

### Denied

Input:

```text
denied
```

Expected output:

```text
Final state: denied
Model calls: 0
Result: None
```

## Run Tests

```bash
python3 -m unittest discover -s 03-GettingStarted/14-sampling/applied-labs/r49-t001 -p "test_*.py"
```

## Scope and Limitations

This is a local simulation using a mock model function.

It does not connect to an actual MCP server, AI model, cloud service, or physical device. The mock response is fixed and does not represent real model performance.

# R49-T001: Client-Consent Gate

## Overview

This example demonstrates a local client-consent gate for model sampling requests.

The request starts in the `pending` state. The client can approve or deny the request.

- Approved: The mock model is called exactly once.
- Denied: The mock model is never called.
- Completed requests cannot receive another decision.

## Requirements

- Python 3
- Python standard library only.
- No external packages required.

## Run the Example

From the repository root, run:

```bash
python3 03-GettingStarted/14-sampling/applied-labs/r49-t001/example.py
```

## Example Inputs and Expected Outputs

### Approved

Input: `approved`

Expected output:

```text
Final state: approved
Model calls: 1
Result: Mock model response
```

### Denied

Input: `denied`

Expected output:

```text
Final state: denied
Model calls: 0
Result: None
```

## Run Tests

```bash
python3 -m unittest discover -s 03-GettingStarted/14-sampling/applied-labs/r49-t001 -p "test_*.py"
```

## Scope and Limitations

This is a local simulation using a mock model function.

It does not connect to an actual MCP server, AI model, cloud service, or physical device. The mock response is fixed and does not represent real model performance.
