"""Risk check before a trade idea, with the OpenAI Agents SDK.

pip install openai-agents
export HPSILAB_API_KEY=hpsi_your_key OPENAI_API_KEY=sk-...
python openai_agents_risk_gate.py NVDA
"""

import asyncio
import os
import sys

from agents import Agent, Runner
from agents.mcp import MCPServerStreamableHttp

INSTRUCTIONS = """You review a proposed stock position before anyone trades it.
1. Call get_pretrade_risk_scan for the ticker. Report failed checks first, then
   warnings, then passes, each with the limit behind its status.
2. If the scan is refused (it needs a paid HPSILab plan), say so and use
   get_monte_carlo and get_iv_radar instead. Never invent a missing number.
3. Do not recommend a position size and do not suggest placing a trade."""


async def main(ticker: str) -> None:
    async with MCPServerStreamableHttp(
        name="hpsilab",
        params={
            "url": "https://hpsilab.com/mcp",
            "headers": {"Authorization": f"Bearer {os.environ['HPSILAB_API_KEY']}"},
        },
    ) as hpsilab:
        agent = Agent(name="Risk reviewer", instructions=INSTRUCTIONS, mcp_servers=[hpsilab])
        result = await Runner.run(agent, f"Review a hypothetical new position in {ticker}.")
        print(result.final_output)


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1] if len(sys.argv) > 1 else "NVDA"))
