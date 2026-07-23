# Earnings Research Prompts

HPSILab does not expose a dedicated earnings-calendar tool. Supply the confirmed earnings date yourself, or ask the client to use another trusted source before invoking HPSILab. Never let the assistant invent an earnings date.

## Pre-earnings volatility brief

```text
Assume AAPL's confirmed earnings date is [DATE]. Use HPSILab's IV radar and
option-pressure tools to prepare a pre-earnings volatility brief. Include IV rank,
IV percentile, regime, skew, expected move, expiry date, max pain, gamma wall,
and pressure zones. Flag any mismatch between the supplied event date and the
returned options expiry. Do not predict the earnings result.
```

## Probabilistic scenario framing

```text
For NVDA, use HPSILab's Monte Carlo, IV radar, and option-pressure tools. Compare
the 30-day simulated range with the options-implied expected move. Explain that
the horizons and methods may differ. Present upside, central, and downside
scenarios without assigning an earnings surprise that the tools did not provide.
```

## Signal stability check

```text
Use HPSILab to analyze META before its confirmed earnings date of [DATE]. Then
retrieve the dedicated AI prediction and IV radar. Identify which metrics are
likely to change rapidly around the event and which are historical summaries.
Do not describe the next-session prediction as an earnings forecast.
```

## Post-earnings review

```text
META reported earnings on [DATE]. Use current HPSILab analysis, IV radar, and
option pressure to describe the post-event setup. Compare current signals only;
do not claim a pre-event value unless it is present in the supplied conversation.
```

