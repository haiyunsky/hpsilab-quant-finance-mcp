from mcp.server.fastmcp import FastMCP
import requests
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("HPSILAB_API_KEY")

mcp = FastMCP("HPSILab MCP Server")

@mcp.tool()
def analyze_stock(symbol: str):
    """
    Analyze stock trends and generate trading signals.

    Args:
        symbol: Stock ticker symbol.

    Returns:
        Quantitative analysis report.
    """
    try:
        response = requests.get(
            f"https://hpsilab.com/api/analyze_stock/{symbol}",
            headers={
                "Authorization": f"Bearer {API_KEY}"
            },
            timeout=30
        )
        response.raise_for_status()
        return response.json()

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

def main():
    mcp.run()

if __name__ == "__main__":
    main()