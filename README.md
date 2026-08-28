# HPSILab Quant Finance MCP Server for Stock & Options Analytics

<!-- mcp-name: io.github.haiyunsky/hpsilab-quant-finance-mcp -->

[![PyPI](https://img.shields.io/pypi/v/hpsilab-quant-finance-mcp?label=PyPI)](https://pypi.org/project/hpsilab-quant-finance-mcp/)
[![CI](https://github.com/haiyunsky/hpsilab-quant-finance-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/haiyunsky/hpsilab-quant-finance-mcp/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](https://github.com/haiyunsky/hpsilab-quant-finance-mcp/blob/main/LICENSE)

HPSILab is an open-source Python quantitative finance MCP server for research on
US equities, ETFs, and supported options. It brings stock signals, implied
volatility, options analytics, Monte Carlo simulation, AI prediction,
backtesting, and risk analysis into ChatGPT, Claude, Cursor, VS Code, and other
MCP clients. Connect once, ask in natural language, and receive structured
results that an assistant can compare and explain.

> Research and educational use only. HPSILab does not provide investment advice
> and does not execute trades.

[Get a Free API Key](https://hpsilab.com/register) · [Pricing](https://hpsilab.com/pricing) · [Tool reference](https://github.com/haiyunsky/hpsilab-quant-finance-mcp/blob/main/docs/tools.md) · [Client setup](https://github.com/haiyunsky/hpsilab-quant-finance-mcp/blob/main/docs/client-setup.md) · [Python SDK](https://pypi.org/project/hpsilab-mcp/)

| | |
| --- | --- |
| **Registry name** | `io.github.haiyunsky/hpsilab-quant-finance-mcp` |
| **Version** | 0.10.0 — a source checkout reports `0.10.0+source` |
| **Transports** | Streamable HTTP (hosted) · stdio (PyPI package) |
| **Remote endpoint** | `https://hpsilab.com/mcp` |
| **Package** | `pip install -U hpsilab-quant-finance-mcp` |
| **Authentication** | Bearer API key, or `HPSILAB_API_KEY` for stdio |
| **Tools** | 10 — nine financial research tools plus `register_account` |

## Connect: hosted Streamable HTTP

Recommended, and requires no local installation.

1. [Register a free account](https://hpsilab.com/register), sign in, and
   generate an API key from Settings.
2. Add the server to your client's **private** configuration, replacing
   `hpsi_your_key`. Never commit a real key or paste one into chat.

The example below is Claude Code's `.mcp.json`; other clients use different
configuration schemas, all covered in
[client setup](https://github.com/haiyunsky/hpsilab-quant-finance-mcp/blob/main/docs/client-setup.md).

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

3. Verify the connection:

```text
Use HPSILab to analyze AAPL. Separate observed metrics from interpretation,
identify conflicting signals, and finish with a concise risk summary.
```

All financial research tools require a valid API key. See
[authentication](https://github.com/haiyunsky/hpsilab-quant-finance-mcp/blob/main/docs/authentication.md)
for key handling and rotation.

## Connect: local stdio

For clients that require a local process:

```bash
pip install -U hpsilab-quant-finance-mcp
```

This example uses the `mcpServers` schema supported by Claude and Cursor; VS
Code and GitHub Copilot use a `servers` schema instead.

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

The client discovers tools with MCP `tools/list` and invokes them with
`tools/call`. See
[local setup](https://github.com/haiyunsky/hpsilab-quant-finance-mcp/blob/main/docs/self-hosting.md)
and
[Python usage](https://github.com/haiyunsky/hpsilab-quant-finance-mcp/blob/main/docs/python-sdk.md),
which also covers calling the tool functions directly from Python.

## Tools

Nine financial research tools, plus `register_account`. Tool names and parameter
meanings are part of the public compatibility contract.

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
| `generate_stock_research_report` | Structured Markdown research report and timestamp | Creates an artifact; not idempotent |
| `register_account` | Account credentials for the authenticated caller | Creates an account and sends email; not idempotent |

Research tools accept one exchange ticker such as `NVDA`, `SPY`, or `BRK.B`;
company names are not accepted. Live results can change between calls. Artifact
tools can consume quota and should not be retried automatically.

Full inputs, outputs, side effects, and tool-selection guidance are in
[docs/tools.md](https://github.com/haiyunsky/hpsilab-quant-finance-mcp/blob/main/docs/tools.md).

### Monte Carlo research example

![PLTR Monte Carlo scenario visualization](https://raw.githubusercontent.com/haiyunsky/hpsilab-quant-finance-mcp/main/assets/pltr-monte-carlo-scenarios.png)

Example visualization of scenario-based Monte Carlo research output. Results
depend on the selected inputs and model assumptions. See
[`get_monte_carlo`](https://github.com/haiyunsky/hpsilab-quant-finance-mcp/blob/main/docs/tools.md#financial-research-tools)
for tool details.

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

Setup guidance covers ChatGPT, Claude, Cursor, VS Code, GitHub Copilot,
Continue, and Kimi. See the
[client setup guide](https://github.com/haiyunsky/hpsilab-quant-finance-mcp/blob/main/docs/client-setup.md)
for each client's transport and configuration format.

## Errors, retries, and limits

Every failure is a structured object with a stable `error_code`, never prose an
agent has to pattern-match. Five refusals matter, because each has a different
remedy:

| `error_code` | Meaning | What resolves it |
| --- | --- | --- |
| `api_key_required` | No key is configured | Registering. Nothing is sent downstream |
| `rate_limited` | Calling too fast (429) | Waiting — `next_actions` carries the seconds |
| `insufficient_credits` | The Credit balance is empty (402) | Adding Credits, or registering for trial Credits |
| `allowance_exhausted` | The free evaluation ceiling is spent (402) | Registering, or verifying an email. Money does not lift it |
| `settlement_unknown` | A payment whose outcome is unconfirmed | Reconciliation. **Do not retry it and do not pay again** |

Without a key the package stops locally, before constructing the downstream
client or sending a request:

```json
{
  "error": "api_key_required",
  "message": "A free API key is required.",
  "register_url": "https://hpsilab.com/register",
  "docs_url": "https://hpsilab.com/developer/v2"
}
```

401 and 402 responses are never retried. A 429 is retried only when it carries a
valid `Retry-After`. Read-only calls use a finite retry budget for timeouts and
recoverable 500/502/503/504 responses; artifact-producing calls are not retried
automatically. The package also applies one process-local safeguard of 10
requests per rolling minute per API key — burst protection, not a quota, since
only the hosted service knows the balance and the plan.

Field-by-field payloads, the Credits circuit breaker, and the reasoning behind
each remedy are in
[docs/authentication.md](https://github.com/haiyunsky/hpsilab-quant-finance-mcp/blob/main/docs/authentication.md)
and
[docs/python-sdk.md](https://github.com/haiyunsky/hpsilab-quant-finance-mcp/blob/main/docs/python-sdk.md).

## Why HPSILab

HPSILab gives assistants typed inputs, structured outputs, ticker validation,
machine-readable errors, and dedicated tools instead of invented metrics. It
supports US-listed equities, ETFs, and supported options data; coverage and
limits depend on the hosted service and plan.

## Safety and license

HPSILab is for research and education only. Outputs may be incomplete, delayed,
or wrong and are not investment, financial, or trading advice. The MCP server has
no brokerage connectivity, order entry, or trade-execution capability.

Licensed under the
[MIT License](https://github.com/haiyunsky/hpsilab-quant-finance-mcp/blob/main/LICENSE).
Contributions are welcome; read
[AGENTS.md](https://github.com/haiyunsky/hpsilab-quant-finance-mcp/blob/main/AGENTS.md)
and
[CONTRIBUTING.md](https://github.com/haiyunsky/hpsilab-quant-finance-mcp/blob/main/CONTRIBUTING.md)
before proposing public schema changes.
