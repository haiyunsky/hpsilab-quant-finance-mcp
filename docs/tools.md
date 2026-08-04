# Tool reference

The publicly documented HPSILab product surface contains nine financial research tools. Tool names and parameter meanings are part of the public compatibility contract.

## Financial research tools

| Tool | Use it for | Key output semantics | Side effects |
| --- | --- | --- | --- |
| `analyze_stock` | A broad, multi-signal view of one ticker | Directional signal, confidence, supporting metrics, and risk context | Read-only and idempotent |
| `get_ai_prediction` | Next-session directional model analysis | Prediction, up probability, confidence, model votes, regime, and signal strength | Read-only and idempotent |
| `get_iv_radar` | Historical context for implied volatility | ATM IV, IV rank, IV percentile, skew, term structure, and regime | Read-only and idempotent |
| `get_option_pressure` | Important options-derived price levels | Max pain, gamma wall, expected move, squeeze targets, and strike concentrations | Read-only and idempotent |
| `get_monte_carlo` | Scenario analysis for a 30-day horizon | Simulated mean, 68% and 90% ranges, upside probability, and downside probability | Read-only and idempotent |
| `get_equity_curve` | Comparing standard strategy backtests | Returns, Sharpe and Sortino ratios, drawdown, win rate, and equity curves | Read-only and idempotent |
| `get_pretrade_risk_scan` | Reviewing a proposed position before a trade | Volatility, beta, VaR, drawdown, position size, exposure, correlation, checks, and warnings | Read-only and idempotent |
| `generate_stock_images` | Creating charts for an analysis workflow | Hosted image artifacts and URLs | Creates artifacts; not idempotent; may consume quota |
| `generate_stock_research_report` | Creating a structured research artifact | Hosted report metadata and content | Creates an artifact; not idempotent; may consume quota |

All nine tools require a valid API key. They accept one US-listed equity or ETF ticker, such as `NVDA`, `AAPL`, `SPY`, or `BRK.B`. Do not pass a company name. Coverage of options-dependent fields varies by symbol and account tier.

Live research output may change between calls. Generated URLs can expire. Clients should surface structured errors and nullable/unavailable fields rather than inventing replacements.

## Choosing a tool

- Start with `analyze_stock` for a broad overview.
- Prefer a dedicated tool when the question is specifically about prediction, volatility, options levels, simulation, backtests, or risk.
- Use artifact tools only when the user explicitly needs a chart or report, and ask before retrying a failed call.
- Never interpret these tools as authorization to place or route an order; no trade execution is available.
