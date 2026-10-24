"""Risk check before a trade idea, with the Claude Agent SDK.

pip install claude-agent-sdk
export HPSILAB_API_KEY=hpsi_your_key ANTHROPIC_API_KEY=sk-ant-...
python claude_agent_sdk_risk_gate.py NVDA
"""

import asyncio
import os
import sys

from claude_agent_sdk import ClaudeAgentOptions, query

SYSTEM_PROMPT = """You review a proposed stock position before anyone trades it.
1. Call get_pretrade_risk_scan for the ticker. Report failed checks first, then
   warnings, then passes, each with the limit behind its status.
2. If the scan is refused (it needs a paid HPSILab plan), say so and use
   get_monte_carlo and get_iv_radar instead. Never invent a missing number.
3. Do not recommend a position size and do not suggest placing a trade."""


async def main(ticker: str) -> None:
    options = ClaudeAgentOptions(
        system_prompt=SYSTEM_PROMPT,
        mcp_servers={
            "hpsilab": {
                "type": "http",
                "url": "https://hpsilab.com/mcp",
                "headers": {"Authorization": f"Bearer {os.environ['HPSILAB_API_KEY']}"},
            }
        },
        # Only the read-only research tools this review needs.
        allowed_tools=[
            "mcp__hpsilab__get_pretrade_risk_scan",
            "mcp__hpsilab__get_monte_carlo",
            "mcp__hpsilab__get_iv_radar",
        ],
    )
    async for message in query(prompt=f"Review a hypothetical new position in {ticker}.", options=options):
        print(message)


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1] if len(sys.argv) > 1 else "NVDA"))
