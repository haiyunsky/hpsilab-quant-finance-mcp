# HPSILab Quant Finance MCP

<!-- mcp-name: io.github.haiyunsky/hpsilab-quant-finance-mcp -->

HPSILab brings structured quantitative research for US equities, ETFs, and supported options into ChatGPT, Claude, Cursor, VS Code, and other MCP clients. It combines stock signals, implied volatility, options positioning, Monte Carlo scenarios, backtests, risk checks, charts, and research reports behind a stable MCP interface. Connect once, ask in natural language, and receive machine-readable results that an assistant can compare and explain.

[Get a Free API Key](https://hpsilab.com/register) · [Pricing](https://hpsilab.com/pricing) · [Python SDK](https://pypi.org/project/hpsilab-mcp/)

> Research and educational use only. HPSILab does not provide investment advice and does not execute trades.

[![PyPI](https://img.shields.io/pypi/v/hpsilab-quant-finance-mcp?label=PyPI)](https://pypi.org/project/hpsilab-quant-finance-mcp/)
[![CI](https://github.com/haiyunsky/hpsilab-quant-finance-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/haiyunsky/hpsilab-quant-finance-mcp/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

## Quick start: Official Remote MCP

The hosted Streamable HTTP service is the recommended setup. It requires no local Python installation and uses one official endpoint:

```json
{
  "mcpServers": {
    "hpsilab": {
      "type": "http",
      "url": "https://hpsilab.com/mcp",
      "headers": {
        "Authorization": "Bearer hpsi_your_key"
      }
    }
  }
}
```

1. [Register a free account](https://hpsilab.com/register), sign in, and generate an API key from Settings.
2. Replace `hpsi_your_key` in your client's private MCP configuration. Never commit or paste a real key into chat.
3. Connect the server and verify it with:

```text
Use HPSILab to analyze AAPL. Separate observed metrics from interpretation,
identify conflicting signals, and finish with a concise risk summary.
```

A valid API key is required for the hosted MCP connection and financial research calls. The header must be named `Authorization` and use the value `Bearer hpsi_your_key`. See [client setup](docs/client-setup.md) and [authentication](docs/authentication.md) for exact configuration and troubleshooting.

### What success looks like

Your client should make the nine publicly documented financial research tools available. A successful first call returns a structured dictionary containing the requested analysis, a status, and the research disclaimer—not an unstructured page that the client must scrape.

If the first call fails, check these three items before changing anything else:

1. The endpoint is exactly the one shown in the configuration above.
2. The authorization value begins with `Bearer ` and contains a currently valid key.
3. The input is an exchange ticker such as `AAPL`, not a company name such as `Apple`.

## Why HPSILab

General-purpose assistants can explain financial concepts, but they should not invent quantitative metrics or silently combine incompatible sources. HPSILab gives assistants a narrow research contract with typed inputs, structured outputs, consistent ticker validation, machine-readable errors, and accurate MCP safety annotations.

The tool surface covers complementary parts of a research workflow: broad signal aggregation, model consensus, volatility context, options-derived levels, probabilistic scenarios, historical strategy behavior, and pre-trade risk. Dedicated tools let the client request only the evidence needed for a question, while report and chart tools create explicit artifacts when a reusable deliverable is required.

The current market scope is US-listed equities, ETFs, and supported options data. Coverage and account limits are governed by the hosted service and selected plan. HPSILab does not connect to a brokerage and cannot place, route, modify, or cancel orders.

## Tools

The public product surface contains **9 financial research tools**.

| Tool | What it returns | Behavior |
| --- | --- | --- |
| `analyze_stock` | Aggregate directional and quantitative stock analysis | Read-only |
| `get_ai_prediction` | Next-session prediction, confidence, and model consensus | Read-only |
| `get_iv_radar` | IV level, rank, percentile, skew, and regime | Read-only |
| `get_option_pressure` | Max pain, gamma walls, expected move, and pressure zones | Read-only |
| `get_monte_carlo` | 30-day simulated distribution and probabilities | Read-only |
| `get_equity_curve` | Strategy backtests and risk-adjusted performance | Read-only |
| `get_pretrade_risk_scan` | Position, exposure, correlation, and risk checks | Read-only |
| `generate_stock_images` | Hosted stock and options chart artifacts | Creates an artifact; not idempotent |
| `generate_stock_research_report` | Structured hosted research report | Creates an artifact; not idempotent |
Research tools accept one exchange ticker such as `NVDA`, `SPY`, or `BRK.B`; company names are not accepted. Live results can change between calls. Artifact tools can consume quota and should not be retried automatically.

Full inputs, outputs, side effects, and tool-selection guidance are in [docs/tools.md](docs/tools.md).

## Copy-ready prompts

### Claude

```text
Use HPSILab to analyze NVDA. Summarize the directional signal, AI model
consensus, IV regime, options pressure, 30-day Monte Carlo range, and the
three most important risks. Distinguish tool data from interpretation.
```

### Cursor

```text
Use HPSILab's IV radar and option-pressure tools for SPY. Compare IV rank,
percentile, skew, expected move, max pain, gamma wall, and pressure zones.
Return a compact table and do not recommend a trade.
```

### ChatGPT

```text
Run the HPSILab pre-trade risk scan for TSLA. Explain every warning or failed
check, preserve unavailable fields as unavailable, and quote the returned
reason instead of guessing. Do not execute or recommend a trade.
```

## Other installation paths

Official Remote MCP is the default. For a client that only supports local stdio:

```bash
pip install -U hpsilab-quant-finance-mcp
```

Set the `HPSILAB_API_KEY` environment variable in the client's private configuration, then launch the console command `hpsilab-quant-finance-mcp`. The package delegates API transport to the separate `hpsilab-mcp` SDK and therefore still needs network access.

Add the installed stdio server to the MCP client's private configuration:

```json
{
  "mcpServers": {
    "hpsilab": {
      "command": "hpsilab-quant-finance-mcp",
      "env": {
        "HPSILAB_API_KEY": "hpsi_your_key"
      }
    }
  }
}
```

Then verify it through the MCP client:

```text
Use HPSILab to get the AI prediction for NVDA and summarize the model consensus.
```

The client discovers tools with MCP `tools/list` and invokes them with `tools/call`; direct Python function calls are not the MCP setup path.

- [Client configuration: ChatGPT, Claude, Cursor, VS Code, Copilot, Continue, and Kimi](docs/client-setup.md)
- [Authentication and API-key handling](docs/authentication.md)
- [Python SDK and direct Python usage](docs/python-sdk.md)
- [Local stdio, source installation, and self-hosting](docs/self-hosting.md)
- [Architecture](docs/architecture.md)

## Supported clients

Official Remote MCP is the preferred path for ChatGPT, Claude, Cursor, VS Code, GitHub Copilot, Continue, and Kimi when their current release supports Streamable HTTP and bearer credentials. Claude, Cursor, VS Code, GitHub Copilot, Continue, and Kimi can also use local stdio where supported; ChatGPT connects to the hosted service. Client capabilities and UI labels evolve, so use the copy-ready configurations and troubleshooting notes in [docs/client-setup.md](docs/client-setup.md).

## Safety and license

HPSILab is for research and education only. Outputs may be incomplete, delayed, or wrong and are not investment, financial, or trading advice. The MCP server has no brokerage connectivity, order entry, or trade-execution capability.

Licensed under the [MIT License](LICENSE). Contributions are welcome; read [AGENTS.md](AGENTS.md) and [CONTRIBUTING.md](CONTRIBUTING.md) before proposing public schema changes.
