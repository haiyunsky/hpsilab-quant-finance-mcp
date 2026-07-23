# Portfolio Research Prompts

The current public tools analyze one ticker per call. Multi-symbol prompts should ask the client to call tools sequentially and compare only common returned fields.

## Watchlist comparison

```text
Use HPSILab to analyze AAPL, MSFT, NVDA, and AMZN sequentially. Create a comparison
table using signal, confidence, IV regime, Monte Carlo downside probability, and
maximum backtest drawdown. Preserve units, mark missing fields as unavailable,
and do not convert this ranking into a buy recommendation.
```

## Concentration review

```text
Run the HPSILab pre-trade risk scan for NVDA. Focus on the exposure and correlation
sections. Explain the assumed position weight and weighting method. If either
section has available=false, quote its reason and tell me what portfolio/watchlist
context is needed instead of fabricating a result.
```

## Diversification research

```text
Run the HPSILab pre-trade risk scan for XLF, then for XLK. Compare the returned
portfolio correlation, concentration flag, volatility, beta, VaR, and drawdown
deltas. Make clear that sequential scans are not the same as a joint portfolio
optimization.
```

## Risk dashboard

```text
For SPY, QQQ, and IWM, call HPSILab's IV radar and Monte Carlo tools sequentially.
Build a dashboard with volatility regime, 68% range, 90% range, probability above
spot, and probability of a 10% drop. Use the response timestamps when available.
```

