# Use HPSILab with Claude

The hosted Streamable HTTP endpoint is recommended for Claude Code. Local stdio is available through the PyPI package for clients that can start local processes.

## Installation

Install a current Claude Code release, or use a Claude surface that supports custom MCP servers. Create an API key at [hpsilab.com](https://hpsilab.com).

For local stdio, also install [`uv`](https://docs.astral.sh/uv/) or the Python package:

```bash
pip install hpsilab-quant-finance-mcp
```

## Configuration

### Claude Code: hosted HTTP

```bash
claude mcp add --transport http --scope user hpsilab https://hpsilab.com/mcp \
  --header "Authorization: Bearer hpsi_your_key"
```

Verify the entry:

```bash
claude mcp get hpsilab
```

For a shareable project configuration, create `.mcp.json` and reference an environment variable rather than committing a secret:

```json
{
  "mcpServers": {
    "hpsilab": {
      "type": "http",
      "url": "https://hpsilab.com/mcp",
      "headers": {
        "Authorization": "Bearer ${HPSILAB_API_KEY}"
      }
    }
  }
}
```

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

Do not commit the literal key. Prefer user-level configuration or your client's supported environment-variable mechanism.

## Example prompts

```text
Use HPSILab to analyze SPY. Compare the broad signal with the AI prediction,
IV regime, options pressure, and Monte Carlo distribution. Call out conflicts.
```

```text
Use HPSILab to produce an options-volatility briefing for TSLA. Include IV rank,
IV percentile, skew, expected move, max pain, gamma wall, and pressure zones.
```

```text
Generate a HPSILab research report for AMD. Do not retry the artifact-producing
tool without asking me because the call is non-idempotent.
```

## Troubleshooting

### Claude reports that the server is disconnected

- Run `claude mcp list` and `claude mcp get hpsilab`.
- Confirm the URL, header, and API key.
- Use `/mcp` inside Claude Code to inspect status.
- Restart Claude Code after changing environment variables.

### A local server closes immediately on Windows

Confirm `uvx` is available on `PATH`. If using `npx` for a bridge in Claude Desktop, native Windows may require a `cmd /c` wrapper. Prefer native hosted HTTP in Claude Code when available.

### The tool response is too large

Ask for a narrower dedicated tool instead of `analyze_stock` or a full report. Claude Code can also warn when MCP output exceeds its configured token threshold.

### Authentication fails

The header value must be `Bearer hpsi_...`. For local stdio, the environment variable must be named exactly `HPSILAB_API_KEY`.

See Anthropic's current [Claude Code MCP documentation](https://docs.anthropic.com/en/docs/claude-code/mcp) for client-level configuration changes.

