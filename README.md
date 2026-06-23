## Installation

```bash
pip install -r requirements.txt
python src/server.py
```

## Reference Implementation

Example MCP server:

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

## Architecture

AI Client
→ HPSI Lab MCP Server
→ HPSI Quant Engine
→ Market Data & Models

The production MCP server is hosted at:

https://hpsilab.com/mcp

This repository contains MCP server definitions, tool schemas, transport examples, and reference implementations.

Production quantitative models, proprietary datasets, and research infrastructure are not included.
