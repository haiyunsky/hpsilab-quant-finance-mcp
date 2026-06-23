from fastmcp import FastMCP

mcp = FastMCP("HPSI Lab MCP Server")

@mcp.tool
def stock_analysis(symbol: str):
    return {"symbol": symbol, "rating": "Buy"}

if __name__ == "__main__":
    mcp.run()
