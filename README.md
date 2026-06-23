# HPSILab MCP Server

Model Context Protocol (MCP) server for quantitative stock analysis powered by HPSI Lab.
Institutional-grade quantitative analysis for AI agents via MCP.

## Overview

HPSILab MCP enables AI agents and MCP-compatible clients to access quantitative equity analysis through a standardized MCP interface.

The server exposes stock analysis tools while abstracting the underlying research infrastructure, factor models, and market data pipelines.

### Features

* Quantitative stock analysis
* Bullish / bearish factor breakdown
* Directional scoring
* Portfolio risk evaluation
* MCP-compatible tool interface
* Local and remote deployment

## Architecture

```text
AI Client
    │
    ▼
HPSILab MCP Server
    │
    ▼
HPSI Quant Engine
    │
    ├── Market Data
    ├── Factor Models
    ├── Signal Engine
    └── Risk Models
```

## Installation

### Clone Repository

```bash
git clone https://github.com/haiyunsky/hpsilab-mcp-server.git

cd hpsilab-mcp-server
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Start Server

```bash
python src/server.py
```

## MCP Configuration

### Local Server

```json
{
  "mcpServers": {
    "hpsilab": {
      "command": "python",
      "args": [
        "src/server.py"
      ]
    }
  }
}
```

### Remote Server

```json
{
  "mcpServers": {
    "hpsilab": {
      "url": "https://hpsilab.com/mcp"
    }
  }
}
```

## Available Tools

### analyze_stock

Analyze a stock using HPSI quantitative models.

Input:

```json
{
  "symbol": "AAPL"
}
```

Example Output:

```json
{
  "symbol": "AAPL",
  "direction": "bullish",
  "score": 82,
  "bullish_factors": [
    "Strong earnings revisions",
    "Positive momentum"
  ],
  "bearish_factors": [
    "Premium valuation"
  ]
}
```

### compare_stocks

Compare multiple securities.

Input:

```json
{
  "symbols": [
    "AAPL",
    "MSFT",
    "NVDA"
  ]
}
```

### portfolio_risk

Evaluate portfolio exposure and risk characteristics.

## Reference Implementation

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("HPSILab MCP Server")

@mcp.tool()
async def analyze_stock(symbol: str):
    return {
        "symbol": symbol,
        "status": "success"
    }

if __name__ == "__main__":
    mcp.run()
```

## Development

Run locally:

```bash
python src/server.py
```

Run tests:

```bash
pytest
```

## Production Service

Production MCP endpoint:

https://hpsilab.com/mcp

The production service may provide additional quantitative models, research signals, and datasets not included in this repository.

## Disclaimer

This repository contains MCP server definitions, tool schemas, transport examples, and reference implementations.

Proprietary quantitative models, research infrastructure, and commercial datasets remain the intellectual property of HPSI Lab and are not included.

## License

MIT License

```
```
