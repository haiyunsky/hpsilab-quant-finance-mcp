# Agent framework examples

Minimal, runnable examples that give an agent a **risk check before it proposes
a trade**, using the hosted HPSILab MCP endpoint (`https://hpsilab.com/mcp`).
Each script is one file and does the same thing in a different framework:

| File | Framework | Install |
| --- | --- | --- |
| `openai_agents_risk_gate.py` | OpenAI Agents SDK | `pip install openai-agents` |
| `claude_agent_sdk_risk_gate.py` | Claude Agent SDK | `pip install claude-agent-sdk` |
| `langgraph_risk_gate.py` | LangChain / LangGraph via `langchain-mcp-adapters` | `pip install langchain-mcp-adapters langgraph "langchain[anthropic]"` |

All three read your key from `HPSILAB_API_KEY` (create one in HPSILab Settings
after [registering](https://hpsilab.com/register)). Scripts cannot do the
interactive OAuth sign-in that Claude Code or a connector UI does, so they use
the Bearer key instead. Never hard-code a key.

```bash
export HPSILAB_API_KEY=hpsi_your_key   # PowerShell: $env:HPSILAB_API_KEY = "hpsi_your_key"
python openai_agents_risk_gate.py NVDA
```

## What the agent is told to do

1. Call `get_pretrade_risk_scan` for the ticker and report every failed check,
   then warnings, then passes, with the limit behind each status.
2. If the scan is refused (it needs a paid plan; a Free account gets a 403 with
   no charge), say so and fall back to `get_monte_carlo` (10-trading-day range)
   and `get_iv_radar` (IV level, rank, skew) instead of guessing.
3. Never recommend a position size or place a trade. HPSILab has no brokerage
   connection; the output is research context for a human or a downstream gate.

Each framework also needs its own model credentials (`OPENAI_API_KEY` for the
OpenAI Agents SDK, `ANTHROPIC_API_KEY` for the Claude Agent SDK and the
LangGraph example).
