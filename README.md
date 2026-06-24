# HPSILab MCP

[![Website](https://img.shields.io/badge/HPSILab-hpsilab.com-orange)](https://hpsilab.com)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![MCP](https://img.shields.io/badge/MCP-Compatible-blue)](https://modelcontextprotocol.io)
[![PyPI](https://img.shields.io/pypi/v/hpsilab-mcp?label=PyPI)](https://pypi.org/project/hpsilab-mcp/)
[![Glama](https://glama.ai/mcp/servers/haiyunsky/hpsilab-mcp-server/badge)](https://glama.ai/mcp/servers/haiyunsky/hpsilab-mcp-server)

⭐ If you find HPSILab useful, please star the repository.

**8 institutional-grade quantitative finance tools for AI agents and MCP clients.**

Analyze stocks using AI forecasting, options positioning, implied volatility intelligence, Monte Carlo simulation, and strategy backtesting — each exposed as a dedicated MCP tool.

**Official Remote MCP Endpoint**

```text
https://hpsilab.com/mcp
```

---

## Quick Start

### Step 1 — Get an API Key

Create an account at [hpsilab.com](https://hpsilab.com) and generate an API key (`hpsi_...`) from the dashboard.

### Step 2 — Which option should I use?

| Option | Setup Time | Best For |
| --- | --- | --- |
| Remote MCP (`https://hpsilab.com/mcp`) | Instant | Most users |
| Python REST SDK (`pip install hpsilab-mcp`) | Instant | Python developers |
| Self-Hosted MCP Server | 2–3 minutes | Self-hosted setups |
| Enterprise Deployment | Custom | Organizations |

### Option 1 — Official Remote MCP Service (Recommended)

Connect directly to the official HPSILab MCP endpoint — no installation required, always up to date.

```text
https://hpsilab.com/mcp
```

### Option 2 — Open Source Self-Hosted MCP Server

```bash
git clone https://github.com/haiyunsky/hpsilab-mcp-server.git
cd hpsilab-mcp-server
pip install -r requirements.txt
python src/hpsilab_mcp_server/server.py
```

---

## Python REST SDK

If you prefer direct REST access without MCP transport, use the official Python SDK. You'll need an API key — see [Step 1](#step-1--get-an-api-key) in Quick Start.

### Installation

```bash
pip install hpsilab-mcp
```

### Quick Start

```python
from hpsilab_mcp import HpsiMcpClient

client = HpsiMcpClient(
    api_key="hpsi_your_key",
    base_url="https://hpsilab.com",
)

# Run all tools in one go
result = client.analyze_stock("NVDA")
print(result)
```

### Available SDK Methods

```python
client.analyze_stock("NVDA")
client.get_ai_prediction("NVDA")
client.get_iv_radar("NVDA")
client.get_option_pressure("NVDA")
client.get_monte_carlo("NVDA")
client.get_equity_curves("NVDA")
client.generate_stock_images("NVDA")
client.generate_stock_research_report("NVDA")
```

### REST Endpoint Mapping

| Method | Endpoint |
| --- | --- |
| `analyze_stock(symbol)` | `GET /api/analyze_stock/{symbol}` |
| `get_ai_prediction(symbol)` | `GET /api/ai_prediction/{symbol}` |
| `get_iv_radar(symbol)` | `GET /api/iv_batch?symbols={symbol}` |
| `get_option_pressure(symbol)` | `GET /api/option_pressure/{symbol}` |
| `get_monte_carlo(symbol)` | `GET /api/monte_carlo/{symbol}` |
| `get_equity_curves(symbol)` | `GET /api/equity_curve/{symbol}` |
| `generate_stock_images(symbol)` | `POST /api/stock_report/{symbol}/images` |
| `generate_stock_research_report(symbol)` | `POST /api/stock_report/{symbol}/research_report` |

### Capability Matrix

| Capability | REST SDK | MCP |
| --- | --- | --- |
| `analyze_stock` | ✅ | ✅ |
| `get_ai_prediction` | ✅ | ✅ |
| `get_iv_radar` | ✅ | ✅ |
| `get_option_pressure` | ✅ | ✅ |
| `get_monte_carlo` | ✅ | ✅ |
| `get_equity_curves` | ✅ | ✅ |
| `generate_stock_images` | ✅ | ✅ |
| `generate_stock_research_report` | ✅ | ✅ |

> **Note:** The Python SDK wraps the hosted REST API and does not implement MCP transport, SSE, streaming, or tool discovery. Use an MCP client when you need assistant-native tool calls or tool discovery.

---

## MCP Client Configuration

### Cursor (Remote MCP)

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

### Claude Desktop / Claude Code (via mcp-remote)

```json
{
  "mcpServers": {
    "hpsilab": {
      "command": "npx",
      "args": [
        "mcp-remote",
        "https://hpsilab.com/mcp",
        "--header",
        "Authorization: Bearer hpsi_your_key"
      ]
    }
  }
}
```

### Self-Hosted (Cursor)

```json
{
  "mcpServers": {
    "hpsilab": {
      "command": "hpsilab-mcp-server"
    }
  }
}
```

---

## Available Tools

All tools accept a single `symbol` parameter: an exchange ticker in uppercase (e.g. `"NVDA"`, `"AAPL"`, `"SPY"`).

### `analyze_stock`

Full institutional-grade analysis — aggregates AI prediction, IV radar, options pressure, Monte Carlo, and backtesting into a single bull/bear verdict.

**Use when:** you need a holistic market view with confidence score and supporting evidence.

**Returns:** `signal`, `confidence_score`, `bullish_factors`, `bearish_factors`, `summary`

---

### `get_iv_radar`

Implied volatility metrics: ATM IV, IV rank (0–100), IV percentile, risk reversal direction, and volatility regime.

**Use when:** you want to assess whether options are cheap or expensive, or identify the current vol regime.

**Returns:** `atm_iv`, `iv_rank`, `iv_percentile`, `risk_reversal`, `volatility_regime`

---

### `get_option_pressure`

Options-market positioning and dealer-hedging pressure zones: max pain, gamma wall, expected move, and squeeze targets.

**Use when:** you need strike-level gravitational targets near expiration or want to size an expected-move trade.

**Returns:** `max_pain`, `gamma_wall`, `expected_move`, `squeeze_target`, `expiry_date`, `pressure_zones`

---

### `get_monte_carlo`

10,000-path GBM Monte Carlo simulation over a 30-day horizon, calibrated with realized volatility and current IV.

**Use when:** you need a probabilistic price range, downside probability estimates, or volatility-adjusted scenarios.

**Returns:** `mean_price`, `range_90`, `range_68`, `prob_above_spot`, `prob_10pct_drop`, `distribution`

---

### `get_ai_prediction`

Ensemble AI directional prediction (gradient-boosted trees + LSTM + quantum VQC) for the next session's move.

**Use when:** you want a data-driven up/down probability with per-model votes and market regime classification.

**Returns:** `prediction`, `up_probability`, `confidence`, `model_votes`, `regime`, `signal_strength`

---

### `get_equity_curves`

Backtested equity curves and risk-adjusted metrics (Sharpe, Sortino, max drawdown, win rate) for standard quant strategies applied to the ticker.

**Use when:** you want historical performance context or need to compare strategy quality across tickers.

**Returns:** `strategies[]` — each with `total_return`, `sharpe_ratio`, `max_drawdown`, `win_rate`, `equity_curve`

---

### `generate_stock_research_report`

Generates a structured markdown research note synthesizing all signal sources, suitable for sharing with investors.

**Use when:** a user asks for a "report" or "write-up" and needs a formatted narrative rather than raw JSON.

**Returns:** `report` (markdown string), `generated_at`

---

### `generate_stock_images`

Returns public URLs for three charts: candlestick price chart, 3-D IV surface, and options flow heatmap. URLs expire after 24 hours.

**Use when:** a user asks to "see" or "visualize" a chart, or you want to embed visuals in a report.

**Returns:** `price_chart_url`, `iv_surface_url`, `options_flow_url`, `expires_at`

---

## Example

```python
# Quick directional verdict
analyze_stock("NVDA")

# Only need vol data
get_iv_radar("NVDA")

# Probabilistic price range
get_monte_carlo("NVDA")
```

**Example `analyze_stock` response:**

```json
{
  "symbol": "NVDA",
  "signal": "Bearish",
  "confidence_score": 42,
  "bullish_factors": [
    "Monte Carlo range midpoint is above current spot.",
    "Option pressure leaves a meaningful upside weekly-high zone."
  ],
  "bearish_factors": [
    "AI prediction gives only a 34.2% probability of an up close.",
    "Max Pain sits below spot, suggesting downward expiry pin pressure.",
    "Risk reversal is put-heavy.",
    "All three AI models point down."
  ],
  "summary": "NVDA screens bearish with a 42/100 direction score."
}
```

---

## Architecture

```text
AI Client (Claude / Cursor / Windsurf / ...)
    ↓  MCP protocol
hpsilab-mcp-server  (this repo)
    ↓  HTTPS REST
HPSILab Quant API  (hpsilab.com)
    ↓
Quant Platform  (IV engine · ML models · Monte Carlo · Backtester)

Python App / Script
    ↓  hpsilab-mcp (pip package)
HPSILab Quant API  (hpsilab.com)
    ↓
Quant Platform  (IV engine · ML models · Monte Carlo · Backtester)
```

---

## Supported MCP Clients

Cursor · Claude Desktop · Claude Code · ChatGPT Agents · Cline · Roo Code · Windsurf · Continue · Any MCP-compatible client

---

## Disclaimer

This software is provided for research and educational purposes only. Nothing contained in this project constitutes investment advice, financial advice, or a recommendation to buy or sell any security. Always perform your own due diligence before making investment decisions.

---

## License

MIT License — Copyright (c) 2026 Haiyun Hu