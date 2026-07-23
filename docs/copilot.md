# Use HPSILab with GitHub Copilot

GitHub Copilot in VS Code uses VS Code's MCP server configuration. This guide focuses on that supported, inspectable workflow.

## Installation

1. Install a current VS Code release and the current GitHub Copilot/Chat experience.
2. Sign in to GitHub and confirm that Agent mode is available under your plan or organization policy.
3. Create an HPSILab API key at [hpsilab.com](https://hpsilab.com).

For local stdio, install `uv` so `uvx` is available.

## Configuration

Open **MCP: Open User Configuration** for a personal setup, or create `.vscode/mcp.json` for a shareable workspace setup.

### Hosted HTTP

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
  "servers": {
    "hpsilab": {
      "type": "stdio",
      "command": "uvx",
      "args": ["hpsilab-quant-finance-mcp"],
      "env": {
        "HPSILAB_API_KEY": "${env:HPSILAB_API_KEY}"
      }
    }
  }
}
```

Start or restart HPSILab from the `mcp.json` editor, open Copilot Chat in Agent mode, and enable HPSILab from **Configure Tools**.

## Example prompts

```text
Use the HPSILab tools to create a concise NVDA research brief. Include the
aggregate signal, IV regime, expected move, Monte Carlo range, and risk warnings.
```

```text
Use only HPSILab's get_equity_curves tool for AMD. Rank the returned strategies
by Sharpe ratio, then compare max drawdown and win rate. Do not infer missing data.
```

```text
Before discussing a new MSFT position, use HPSILab's risk scan and explain each
sizing, exposure, and correlation field in plain language.
```

## Troubleshooting

### Copilot does not offer HPSILab tools

- Use Agent mode, not a mode that disables tools.
- Open **Configure Tools** and select the HPSILab tools.
- Confirm the MCP server is running in **MCP: List Servers**.
- Check whether organization policy blocks custom MCP servers.

### The API key is not available

For `${env:HPSILAB_API_KEY}`, set the variable before launching VS Code and restart the application. For a shared repository, prefer a password input variable so secrets never enter source control.

### Calls time out

Broad analysis and artifact generation can take longer than a single-metric call. Retry a read-only call once, but ask before retrying report or image generation because those tools are non-idempotent.

### Tools work in VS Code but not another Copilot surface

MCP availability differs across Copilot surfaces and versions. Use the VS Code setup above as the reference path and consult the current GitHub or VS Code documentation for bridging or CLI support.

See the current [VS Code MCP server documentation](https://code.visualstudio.com/docs/agent-customization/mcp-servers).

