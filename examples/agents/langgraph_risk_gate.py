"""Risk check before a trade idea, with LangGraph and langchain-mcp-adapters.

pip install langchain-mcp-adapters langgraph "langchain[anthropic]"
export HPSILAB_API_KEY=hpsi_your_key ANTHROPIC_API_KEY=sk-ant-...
python langgraph_risk_gate.py NVDA
"""

import asyncio
import os
import sys

from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent

INSTRUCTIONS = """You review a proposed stock position before anyone trades it.
1. Call get_pretrade_risk_scan for the ticker. Report failed checks first, then
   warnings, then passes, each with the limit behind its status.
2. If the scan is refused (it needs a paid HPSILab plan), say so and use
   get_monte_carlo and get_iv_radar instead. Never invent a missing number.
3. Do not recommend a position size and do not suggest placing a trade."""

READ_ONLY = {"get_pretrade_risk_scan", "get_monte_carlo", "get_iv_radar"}


async def main(ticker: str) -> None:
    client = MultiServerMCPClient(
        {
            "hpsilab": {
                "transport": "streamable_http",
                "url": "https://hpsilab.com/mcp",
                "headers": {"Authorization": f"Bearer {os.environ['HPSILAB_API_KEY']}"},
            }
        }
    )
    tools = [tool for tool in await client.get_tools() if tool.name in READ_ONLY]
    agent = create_react_agent("anthropic:claude-sonnet-5-5", tools, prompt=INSTRUCTIONS)
    result = await agent.ainvoke({"messages": [("user", f"Review a hypothetical new position in {ticker}.")]})
    print(result["messages"][-1].content)


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1] if len(sys.argv) > 1 else "NVDA"))
