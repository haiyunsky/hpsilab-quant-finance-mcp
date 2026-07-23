# Stock Analysis Prompts

Copy these prompts into any configured MCP client. Replace tickers as needed.

## Executive overview

```text
Use HPSILab to analyze NVDA. Return:
1. overall signal and confidence;
2. strongest bullish and bearish factors;
3. AI model consensus;
4. IV regime and important options levels;
5. 30-day Monte Carlo 68% and 90% ranges;
6. the three most important limitations or risks.
Separate tool data from your interpretation. Do not recommend a trade.
```

## Conflicting-signal review

```text
Analyze META with HPSILab. Focus on disagreement: identify where the aggregate
signal, AI prediction, implied volatility, options pressure, and backtests point
in different directions. Explain which observations are short-horizon versus
historical. Do not force a bullish or bearish conclusion.
```

## Compare two tickers sequentially

```text
Use HPSILab to analyze MSFT and GOOGL one ticker at a time. Build a comparison
table using only fields returned for both symbols. Compare confidence, volatility
regime, Monte Carlo downside probability, and backtest drawdown. State the data
timestamp or freshness information when provided.
```

## ETF market briefing

```text
Use HPSILab to analyze SPY. Write a five-bullet market briefing covering signal,
regime, options positioning, probability range, and risk. Keep numerical values
in their returned units and do not infer macroeconomic causes that the tools did
not provide.
```

