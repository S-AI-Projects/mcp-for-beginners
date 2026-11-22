# Deploying MCP Servers

> [!NOTE]
> Configuration examples that use a `/sse` endpoint target the legacy HTTP+SSE
> transport. MCP `2026-07-28` remote servers use Streamable HTTP, normally at a
> server-defined endpoint such as `/mcp`.

Deploying your MCP server allows others to access its tools and resources beyond your local environment. There are several deployment strategies to consider, depending on your requirements for scalability, reliability, and ease of management. Below you'll find guidance for deploying MCP servers locally, in containers, and to the cloud.

## Overview

This lesson covers how to deploy your MCP Server app.

## Learning Objectives

By the end of this lesson, you will be able to:

- Evaluate different deployment approaches.
- Deploy your app.

## Local development and deployment

If your server is meant to be consumed by running on users machine, you can follow the following steps:

1. **Download the server**. If you didn't write the server, then download it first to your machine. 
1. **Start the server process**: Run your MCP server application 

For SSE (not needed for stdio type server)

1. **Configure networking**: Ensure the server is accessible on the expected port 
1. **Connect clients**: Use local connection URLs like `http://localhost:3000`

## Cloud Deployment

MCP servers can be deployed to various cloud platforms:

- **Serverless Functions**: Deploy lightweight MCP servers as serverless functions
- **Container Services**: Use services like Azure Container Apps, AWS ECS, or Google Cloud Run
- **Kubernetes**: Deploy and manage MCP servers in Kubernetes clusters for high availability

### Example: Azure Container Apps

Azure Container Apps support deployment of MCP Servers. It's still a work in progress and it currently supports SSE servers.

Here's how you can go about it:

1. Clone a repo:

  ```sh
  git clone https://github.com/anthonychu/azure-container-apps-mcp-sample.git
  ```

1. Run it locally to test things out:

  ```sh
  uv venv
  uv sync

  # linux/macOS
  export API_KEYS=<AN_API_KEY>
  # windows
  set API_KEYS=<AN_API_KEY>

  uv run fastapi dev main.py
  ```

1. To try it locally, create an *mcp.json* file in a *.vscode* directory and add the following content:

  ```json
  {
      "inputs": [
          {
              "type": "promptString",
              "id": "weather-api-key",
              "description": "Weather API Key",
              "password": true
          }
      ],
      "servers": {
          "weather-sse": {
              "type": "sse",
              "url": "http://localhost:8000/sse",
              "headers": {
                  "x-api-key": "${input:weather-api-key}"
              }
          }
      }
  }
  ```

  Once the SSE server is started, you can click the play icon in the JSON file, you should now see tools on the server being picked up by GitHub Copilot, see the Tool icon. 

1. To deploy, run the following command:

  ```sh
  az containerapp up -g <RESOURCE_GROUP_NAME> -n weather-mcp --environment mcp -l westus --env-vars API_KEYS=<AN_API_KEY> --source .
  ```

There you have it, deploy it locally, deploy it to Azure through these steps.

## 🧪 Applied Lab: Tool Dispatch Benchmarking Across Deployment Profiles (Task R49-T029)

When deploying MCP servers across various infrastructure targets (minimal CLI sidecars, containerized microservices, or enterprise audit platforms), deployment profiles must balance memory retention and diagnostic overhead while strictly guaranteeing contract correctness.

The complete local implementation is available at:
👉 **[applied-labs/r49-t029/example.py](./applied-labs/r49-t029/example.py)**  
👉 **[applied-labs/r49-t029/test_example.py](./applied-labs/r49-t029/test_example.py)**

> [!NOTE]
> **Simulation / Mock Notice**: This is a local contract fixture evaluating controlled telemetry profiles and batch sizes in-process. It does not measure real-world network transmission, remote cloud hosting latency, or trained-model inference accuracy.

### Exact Invocation

Run the configuration benchmarking demonstration:
```bash
python3 03-GettingStarted/09-deployment/applied-labs/r49-t029/example.py
```

Run the unit test suite:
```bash
python3 -m unittest discover -s 03-GettingStarted/09-deployment/applied-labs/r49-t029 -p "test_*.py"
```

### Controlled Configuration Comparison

| Profile Name | Target Environment | Telemetry Buffer | Correctness | Observed Trade-off |
|---|---|---|---|---|
| `minimal_embedded` | CLI / Sidecar | 0 records | **100.0%** | Zero memory overhead; no diagnostic history retained. |
| `standard_container` | Azure Container Apps | 50 records | **100.0%** | Bounded memory buffer; captures operational success/failure status. |
| `enterprise_diagnostic` | Audited Enterprise Platform | 500 records | **100.0%** | Maximum diagnostic fidelity; full request/response payload cloning. |

### Contract Verification & Expected Output

#### Scenario 1: Valid Normal Dispatch
* `add(2, 3)` → `{"success": true, "result": 5, "error": null}`
* `multiply(2, 3)` → `{"success": true, "result": 6, "error": null}`

#### Scenario 2: Structured Error & Isolation
* Unknown tool (`"divide"`): returns `UNKNOWN_TOOL` structured error.
* Invalid argument (`a: "2"`): returns `INVALID_ARGUMENT` structured error.
* Failure isolation: A failed call halts processing immediately, executing zero tool handlers (`add_call_count == 0`, `multiply_call_count == 0`).

## Additional Resources

- [Azure Functions + MCP](https://learn.microsoft.com/en-us/samples/azure-samples/remote-mcp-functions-dotnet/remote-mcp-functions-dotnet/)
- [Azure Container Apps article](https://techcommunity.microsoft.com/blog/appsonazureblog/host-remote-mcp-servers-in-azure-container-apps/4403550)
- [Azure Container Apps MCP repo](https://github.com/anthonychu/azure-container-apps-mcp-sample)


## What's Next

- Next: [Advanced Server Topics](../10-advanced/README.md)