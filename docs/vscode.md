# Use HPSILab with VS Code

VS Code can connect to the hosted HPSILab endpoint or start the local stdio package. MCP tools are available from Chat in Agent mode.

## Installation

1. Install a current VS Code release with MCP and Chat/Agent support.
2. Sign in to the provider used by your Chat experience.
3. [Register](https://hpsilab.com/register), sign in, and generate an API key in Settings.
4. For local stdio, install `uv` so `uvx` is available.

## Configuration

Open the Command Palette and run **MCP: Add Server**, or create `.vscode/mcp.json`.

### Hosted HTTP

This workspace configuration prompts for the key rather than storing it in Git:

```json
{
  "inputs": [
    {
      "type": "promptString",
      "id": "hpsilabApiKey",
      "description": "HPSILab API key",
      "password": true
    }
  ],
  "servers": {
    "hpsilab": {
      "type": "http",
      "url": "https://hpsilab.com/mcp",
      "headers": {
        "Authorization": "Bearer ${input:hpsilabApiKey}"
      }
    }
  }
}
```

### Local stdio

```json
{
  "inputs": [
    {
      "type": "promptString",
      "id": "hpsilabApiKey",
      "description": "HPSILab API key",
      "password": true
    }
  ],
  "servers": {
    "hpsilab": {
      "type": "stdio",
      "command": "uvx",
      "args": ["hpsilab-quant-finance-mcp"],
      "env": {
        "HPSILAB_API_KEY": "${input:hpsilabApiKey}"
      }
    }
  }
}
```

Open Chat, choose **Agent**, select **Configure Tools**, and enable the HPSILab tools relevant to the request.

## Example prompts

```text
#analyze_stock Analyze QQQ and summarize the signal, confidence, strongest
supporting evidence, and material risks.
```

```text
Use HPSILab to compare the IV regime and options pressure for AAPL. Explain the
metrics for a developer who understands finance but is new to options flow.
```

```text
Run a Monte Carlo analysis for META and turn the returned 68% and 90% ranges
and downside probability into a concise scenario table.
```

## Troubleshooting

### The tools do not appear

- Confirm Chat is in Agent mode.
- Select **Configure Tools** and enable HPSILab.
- Run **MCP: List Servers**, choose HPSILab, and restart it.
- Save `mcp.json` and accept the server trust prompt.

### The server shows an error icon

Run **MCP: List Servers → HPSILab → Show Output** and inspect the MCP log. Common causes are an invalid JSON file, a missing `uvx`, or a rejected API key.

### A team member cannot use the workspace configuration

Do not put the real key in `.vscode/mcp.json`. Keep the input-variable configuration in Git; each user supplies their own key. Enterprise policy can also restrict third-party MCP servers.

### The agent selects the wrong tool

Enable only the relevant HPSILab tools for the request, or explicitly name a tool with `#`. A smaller active tool set improves selection accuracy.

See Microsoft's current [VS Code MCP server guide](https://code.visualstudio.com/docs/agent-customization/mcp-servers).
