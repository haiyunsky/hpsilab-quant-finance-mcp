---
name: stock-research
description: Research a US stock or ETF with HPSILab. Use when the user asks to analyze a ticker, wants a bull and bear view, a likely price range over the next couple of weeks, the model's next-day direction, how a strategy has done historically, chart images, or a written research report.
---

# Stock research

Use the HPSILab connector's tools. If they are not available, tell the user to connect HPSILab (https://hpsilab.com/connect) and stop; never invent figures. Pass one official ticker per call, and use the parameter names in each tool's own input schema (some take `symbol`, some take `ticker`).

Pick the tools that answer the question:

| The user wants | Call | Horizon to state |
| --- | --- | --- |
| A general view, "analyze X" | `analyze_stock` | mixed; name each part's source |
| A likely price range | `get_monte_carlo` | the next 10 trading days |
| The model's direction | `get_ai_prediction` | the next trading day only |
| How the strategy has done | `get_equity_curve` | historical backtest, not a forecast |
| Chart images | `generate_stock_images` | the data date |
| A written report | `generate_stock_research_report` | the data date |

For an open-ended "analyze X", start with `analyze_stock`, then add `get_monte_carlo` for the range. Keep each number with its own horizon; never move a figure from one horizon to another.

`generate_stock_images` and `generate_stock_research_report` create hosted files and use the user's plan quota, so confirm before calling them unless the user asked for charts or a report, and do not retry them automatically.

When you answer, separate what the tools returned from your interpretation, list the strongest points on each side, and give the data date. If a tool fails or is gated, say which one and why, and continue with the others. Do not tell the user to buy or sell, and do not present a range or a probability as a guarantee. Never ask for, print or store an API key.
