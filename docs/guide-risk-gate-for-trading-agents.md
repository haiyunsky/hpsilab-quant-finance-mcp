# Give your trading agent a risk check before it proposes a trade

An LLM agent that can read market data will happily talk itself into a trade.
The fix is not a better prompt; it is a step the agent cannot skip: before any
position is proposed, it has to fetch a risk scan with fixed limits and report
what failed. This guide wires that step into an agent through MCP in a few
lines, using HPSILab's hosted server.

## What the check returns

`get_pretrade_risk_scan` looks at one ticker against SPY and returns numbers
with explicit pass / warn / fail limits, for example (NVDA, 2026-10-23 data):

| Check | Value | Limit | Status |
| --- | --- | --- | --- |
| Market exposure (beta vs SPY) | 1.93 | warn > 1.3, fail > 2.0 | WARN |
| Annualized volatility | 38% | warn > 40%, fail > 70% | PASS |
| 1-year max drawdown | 20% | warn > 25%, fail > 45% | PASS |
| Average daily turnover | $23.8B | warn < $5M, fail < $0.5M | PASS |

It also adds a 10-trading-day simulated return range, sector exposure and
correlation against a portfolio proxy, and a `methodology` block that states
every limit, so the agent can quote the rule instead of paraphrasing it.

The scan needs a paid plan. Without one, the same agent can fall back to two
free tools: `get_monte_carlo` (10-trading-day price range and odds of finishing
higher) and `get_iv_radar` (implied-volatility level, rank and 25-delta skew).

## Connect

In Claude Code, one line, and you sign in with OAuth on first use:

```bash
claude mcp add --transport http hpsilab https://hpsilab.com/mcp
```

In code, send an API key from HPSILab Settings as a Bearer header. With the
OpenAI Agents SDK:

```python
from agents import Agent, Runner
from agents.mcp import MCPServerStreamableHttp

async with MCPServerStreamableHttp(
    name="hpsilab",
    params={
        "url": "https://hpsilab.com/mcp",
        "headers": {"Authorization": f"Bearer {os.environ['HPSILAB_API_KEY']}"},
    },
) as hpsilab:
    agent = Agent(name="Risk reviewer", instructions=INSTRUCTIONS, mcp_servers=[hpsilab])
    result = await Runner.run(agent, "Review a hypothetical new position in NVDA.")
```

The same agent for the Claude Agent SDK and for LangGraph is in
[examples/agents](https://github.com/haiyunsky/hpsilab-quant-finance-mcp/tree/main/examples/agents).

## The instructions that make it a gate

```text
You review a proposed stock position before anyone trades it.
1. Call get_pretrade_risk_scan for the ticker. Report failed checks first, then
   warnings, then passes, each with the limit behind its status.
2. If the scan is refused (it needs a paid plan), say so and use
   get_monte_carlo and get_iv_radar instead. Never invent a missing number.
3. Do not recommend a position size and do not suggest placing a trade.
```

Order matters: failures before passes, so a bullish narrative cannot bury a
warning. "Never invent a missing number" matters more: when a field is null,
the agent should say it is unavailable rather than estimate it.

## Where the gate really belongs

A prompt is guidance, not control. In production the check should sit in your
code between the model and the broker: the model proposes, your code calls the
scan, and a FAIL blocks the order with a logged reason. HPSILab's own
paper-trading agent works that way, and the MCP tool gives you the same data
to build it.

HPSILab is research only: it has no brokerage connection and cannot place
orders. Outputs can be delayed or wrong and are not investment advice.

Links: [repository](https://github.com/haiyunsky/hpsilab-quant-finance-mcp) ·
[tool reference](https://github.com/haiyunsky/hpsilab-quant-finance-mcp/blob/main/docs/tools.md) ·
[hpsilab.com](https://hpsilab.com/?utm_source=github&utm_medium=guide&utm_campaign=risk-gate)
