# HPSILab MCP Server

Quantitative stock analysis MCP server powered by AI prediction, options analytics, volatility intelligence, Monte Carlo simulation, and strategy backtesting.

HPSILab MCP Server enables AI assistants such as Cursor, Claude Desktop, Cline, Roo Code, and other MCP-compatible clients to perform institutional-style quantitative stock analysis.

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
* Cline
* Roo Code
* Windsurf
* Continue
* Any MCP-compatible client

---

## Installation

Clone the repository:

```bash
git clone https://github.com/haiyunsky/hpsilab-mcp-server.git
cd hpsilab-mcp-server
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## Running the Server

Start the MCP server:

```bash
python src/server.py
```

The server runs using the MCP stdio transport and waits for MCP client connections.

---

## MCP Client Configuration

### Cursor

Add the following to your Cursor MCP configuration:

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

### Claude Desktop

Add the following to your Claude Desktop MCP configuration:

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

Performs quantitative stock analysis using multiple models and market intelligence systems.

#### Parameters

| Name   | Type   | Description                                           |
| ------ | ------ | ----------------------------------------------------- |
| symbol | string | Stock ticker symbol (e.g. NVDA, AAPL, TSLA, SPY, QQQ) |

#### Models Used

The analysis may incorporate:

* AI Prediction Engine
* Volatility Radar
* Option Pressure Map
* Monte Carlo Simulation
* Strategy Backtesting Engine

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

## Response Fields

| Field            | Type    | Description                        |
| ---------------- | ------- | ---------------------------------- |
| symbol           | string  | Stock ticker                       |
| signal           | string  | Bullish, Bearish, or Neutral       |
| confidence_score | integer | Direction confidence score (0-100) |
| bullish_factors  | array   | Positive supporting signals        |
| bearish_factors  | array   | Negative supporting signals        |
| summary          | string  | Human-readable analysis summary    |

---

## Quantitative Models

### AI Prediction

Predicts next-day direction probability using multiple machine learning models.

Outputs may include:

* Probability of upward move
* Model consensus
* Suggested risk levels
* Sentiment indicators

### IV Radar

Analyzes option market volatility metrics including:

* ATM Implied Volatility
* IV Rank
* IV Percentile
* Risk Reversal
* Volatility Regime

### Option Pressure Map

Analyzes dealer positioning and option flow:

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

### Strategy Backtesting

Evaluates historical strategy performance:

* Total Return
* Sharpe Ratio
* Maximum Drawdown
* Win Rate
* Profit/Loss Ratio

---

## Use Cases

Examples:

* Analyze NVDA directional bias
* Evaluate bullish vs bearish evidence
* Study options market positioning
* Estimate volatility risk
* Explore probabilistic price scenarios
* Generate quantitative market insights

---

## Hosted Platform

HPSILab provides quantitative market research and analytics services.

Website:

https://hpsilab.com

---

## Disclaimer

This software is provided for research and educational purposes only.

Nothing contained in this project constitutes investment advice, financial advice, trading advice, or a recommendation to buy or sell any security.

Always perform your own due diligence before making investment decisions.

---

## License

MIT License

Copyright (c) 2026 Haiyun Hu
