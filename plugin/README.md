# HPSILab Quant Research

Stock and options research for US equities inside Claude: check a trade's risk before you buy, read how the options market is priced and positioned, and get Monte Carlo price ranges, backtests, chart images and research reports. HPSILab is for research and education only. It does not give personalized investment advice, has no brokerage connection and never places trades.

## What's inside

- **The HPSILab connector** (`.mcp.json`), the remote MCP server at `https://hpsilab.com/mcp`. Claude asks you to sign in with your HPSILab account through OAuth the first time you use it; there is no API key to paste.
- **Three skills** that tell Claude when and how to use the connector's tools:
  - `pre-trade-check`: before buying or adding to a position, runs the pre-trade risk scan and reports every check that passes, warns or fails, with the rule behind it.
  - `options-check`: implied volatility, IV rank and skew, plus max pain, the gamma and call/put walls and the weekly expected move for the nearest expiry.
  - `stock-research`: stock analysis, a 10-trading-day Monte Carlo range, the next-day model view, backtests, chart images and written reports.

## Use it

Install the plugin, connect HPSILab from the plugin's Connectors tab and sign in. You need an HPSILab account, which is free to create at https://hpsilab.com/register; the pre-trade risk scan needs a paid plan. Then ask, for example:

- "Before I buy NVDA at 10% of my portfolio, run a pre-trade risk check."
- "How expensive are SPY options right now? Where are max pain and the gamma wall?"
- "Analyze AAPL and give me a 10-day price range."

## Data

The plugin itself runs no code and stores nothing. When Claude calls a tool, the connector sends the tool's arguments (such as a ticker symbol or a position size) to HPSILab at `https://hpsilab.com/mcp` under your signed-in account, and HPSILab returns research results. HPSILab does not receive your conversation. Calls are logged with your account for usage metering and security, and each pre-trade check of a US stock or ETF is saved to your check history on hpsilab.com. See the privacy policy at https://hpsilab.com/privacy.

## Support

support@hpsilab.com · https://hpsilab.com/connect
