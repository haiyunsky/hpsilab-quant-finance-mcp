# Use HPSILab with Cursor

Cursor can connect to the hosted Streamable HTTP endpoint or start the local stdio package.

## Installation

1. Install a current Cursor release with MCP support.
2. [Register](https://hpsilab.com/register), sign in, and generate an API key in Settings.
3. For local stdio, install `uv` so `uvx` is available.

## Configuration

Open Cursor's MCP settings and add a server, or edit the supported user/workspace MCP JSON file for your Cursor version.

### Hosted HTTP

```json
{
  "mcpServers": {
    "hpsilab": {
      "url": "https://hpsilab.com/mcp",
      "headers": {
        "Authorization": "Bearer hpsi_your_key"
      }
    }
  }
}
```

Store the real key only in a private user-level configuration. Do not commit it to a repository.

### Local stdio

```json
{
  "mcpServers": {
    "hpsilab": {
      "command": "uvx",
      "args": ["hpsilab-quant-finance-mcp"],
      "env": {
        "HPSILAB_API_KEY": "hpsi_your_key"
      }
    }
  }
}
```

After saving, refresh the MCP server and confirm that the publicly documented financial research tools are visible.

## Example prompts

```text
Use HPSILab to analyze AMZN. Return a compact table of direction, confidence,
volatility regime, options levels, simulated range, and key caveats.
```

```text
Use HPSILab's IV radar and option-pressure tools for SPY. Explain what the
combination implies about current uncertainty without making a trade recommendation.
```

```text
Run the HPSILab pre-trade risk scan for TSLA. Treat any unavailable exposure or
correlation data as unavailable and quote the response's reason.
```

## Troubleshooting

### No tools are discovered

- Confirm the JSON property is `mcpServers` for your Cursor configuration format.
- Confirm the endpoint has no trailing typo and uses HTTPS.
- Restart the MCP server or Cursor after editing configuration.
- Check Cursor's MCP logs for HTTP or process-start errors.

### The hosted server returns an authentication error

The header must be named `Authorization`, and its value must begin with `Bearer `. Regenerate the key if it was exposed or revoked.

### `uvx` is not found

Install `uv`, restart Cursor so it receives the updated `PATH`, or use the absolute path to `uvx`. Alternatively, use the hosted endpoint.

### Cursor repeatedly calls an artifact tool

Stop the run and instruct the agent not to retry `generate_stock_images` or `generate_stock_research_report` without confirmation. Both are non-idempotent.
