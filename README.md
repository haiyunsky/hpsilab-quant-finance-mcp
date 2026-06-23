# HPSILab MCP

[![Website](https://img.shields.io/badge/HPSILab-hpsilab.com-orange)](https://hpsilab.com)

[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

[![MCP](https://img.shields.io/badge/MCP-Compatible-blue)](https://modelcontextprotocol.io)

⭐ If you find HPSILab useful, please star the repository.

Institutional-grade quantitative stock analysis for AI assistants and MCP clients.

Analyze stocks using AI forecasting, options positioning, volatility intelligence, Monte Carlo simulation, and strategy backtesting through a single MCP tool.

**Official Remote MCP Endpoint**

```text
https://hpsilab.com/mcp
```

HPSILab combines AI prediction, options analytics, volatility intelligence, Monte Carlo simulation, and strategy backtesting into a unified MCP experience.

Supported by HPSILab's quantitative research platform and available as both a hosted Remote MCP service and an open-source self-hosted MCP server.

---

## 🚀 Quick Start

## Which Option Should I Use?

| Option                                 | Setup Time  | Best For      |
| -------------------------------------- | ----------- | ------------- |
| Remote MCP (`https://hpsilab.com/mcp`) | Instant     | Most users    |
| Self-Hosted MCP Server                 | 2-3 minutes | Developers    |
| Enterprise Deployment                  | Custom      | Organizations |

### Option 1 — Official Remote MCP Service (Recommended)

Connect directly to the official HPSILab MCP endpoint:

```text
https://hpsilab.com/mcp
```

Benefits:

* No installation required
* Always up to date
* Managed infrastructure
* Fastest setup experience
* Works anywhere MCP is supported

### Option 2 — Open Source Self-Hosted MCP Server

Clone the repository:

```bash
git clone https://github.com/haiyunsky/hpsilab-mcp-server.git
cd hpsilab-mcp-server
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Start the server:

```bash
python src/server.py
```

The server runs using MCP stdio transport and connects to HPSILab quantitative APIs.

Ideal for:

* Developers
* Auditing source code
* Enterprise deployments
* Internal AI platforms
* Custom MCP workflows

---

## Architecture

### Remote MCP

```text
AI Client
    ↓
https://hpsilab.com/mcp
    ↓
HPSILab Quant Platform
```

### Self-Hosted MCP

```text
AI Client
    ↓
hpsilab-mcp-server
    ↓
HPSILab Quant API
    ↓
HPSILab Quant Platform
```

---

## Keywords

MCP Server, Stock Analysis, Quantitative Finance, AI Trading, Options Analytics, Volatility Analysis, Monte Carlo Simulation, Backtesting, Claude MCP, Cursor MCP, ChatGPT MCP

---

## Features

* 🤖 AI stock prediction
* 📡 Implied volatility analysis
* 🧲 Option pressure analysis
* 🎲 Monte Carlo simulation
* 📊 Strategy backtesting
* 📈 Bullish/Bearish signal generation
* ⚡ Confidence scoring
* 📉 Risk assessment
* 🔍 Multi-model signal aggregation

---

## Supported MCP Clients

* Cursor
* Claude Desktop
* Claude Code
* ChatGPT Agents
* Cline
* Roo Code
* Windsurf
* Continue
* Any MCP-compatible client

---

## MCP Client Configuration

### Get an API Key

Create a free HPSILab account:

https://hpsilab.com

Generate your API key from the dashboard and use it in your MCP client configuration.

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

### Cursor (Self Hosted)

```json

{
  "mcpServers": {
    "hpsilab": {
      "command": "hpsilab-mcp-server"
    }
  }
}

```

### Claude Desktop

```json
{
  "mcpServers": {
    "hpsilab": {
      "command": "python",
      "args": ["src/server.py"]
    }
  }
}
```

---

## Available Tools

### analyze_stock

Performs institutional-style quantitative stock analysis using multiple models and market intelligence systems.

#### Parameters

| Name   | Type   | Description                                            |
| ------ | ------ | ------------------------------------------------------ |
| symbol | string | Stock ticker symbol (NVDA, AAPL, TSLA, SPY, QQQ, etc.) |

---

## Quantitative Models

### AI Prediction Engine

Predicts directional probability using multiple machine learning models.

Outputs may include:

* Probability of upward move
* Model consensus
* Risk indicators
* Confidence scoring

### IV Radar

Analyzes:

* ATM Implied Volatility
* IV Rank
* IV Percentile
* Risk Reversal
* Volatility Regime

### Option Pressure Map

Analyzes:

* Max Pain
* Gamma Wall
* Expected Move
* Squeeze Targets
* Expiry Pressure Zones

### Monte Carlo Simulation

Projects probabilistic future price paths:

* Probability ranges
* Expected outcomes
* Support levels
* Resistance levels
* Volatility-adjusted scenarios

### Strategy Backtesting Engine

Evaluates:

* Total Return
* Sharpe Ratio
* Maximum Drawdown
* Win Rate
* Profit/Loss Ratio

---

## Example Request

```python
analyze_stock("NVDA")
```

---

## Example Response

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

## Use Cases

* Analyze directional bias for any stock
* Evaluate bullish versus bearish evidence
* Study options market positioning
* Estimate volatility risk
* Explore probabilistic price scenarios
* Generate institutional-style market insights

---

## Why HPSILab?

Most stock analysis tools focus on a single signal.

HPSILab combines:

* AI forecasts
* Options positioning
* Volatility analytics
* Quantitative simulations
* Historical strategy validation

to generate a unified market view with transparent supporting evidence.

---

## Official HPSILab Services

### Website

```text
https://hpsilab.com
```

### Remote MCP Endpoint

```text
https://hpsilab.com/mcp
```

---

## Disclaimer

This software is provided for research and educational purposes only.

Nothing contained in this project constitutes investment advice, financial advice, trading advice, or a recommendation to buy or sell any security.

Always perform your own due diligence before making investment decisions.

---

## License

MIT License

Copyright (c) 2026 Haiyun Hu
