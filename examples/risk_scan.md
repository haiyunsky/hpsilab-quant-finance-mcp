# Pre-Trade Risk Scan Prompts

## Complete review

```text
Run HPSILab's pre-trade risk scan for NVDA. Report:
- market regime and confidence;
- every before/after risk delta with units;
- every sizing check and its pass/warn/fail status;
- sector and symbol exposure changes;
- average, highest, and lowest portfolio correlations;
- the 90% forward-return range and mean.
Quote returned reasons for unavailable sections. Do not recommend position size.
```

## Warning-first summary

```text
Use HPSILab to scan TSLA before a hypothetical trade. Start with failed checks,
then warnings, then passed checks. Explain the threshold behind each status when
provided. Do not soften or omit a warning because the aggregate stock signal is
bullish.
```

## Risk scan versus Monte Carlo

```text
For AMD, run the pre-trade risk scan and Monte Carlo tools. Compare their ranges,
horizons, and downside measures without assuming they use the same model. Explain
why a portfolio-aware risk result can differ from a standalone price simulation.
```

## Missing portfolio context

```text
Run the HPSILab risk scan for MSFT. If exposure or correlation is unavailable,
show the exact reason returned, list which other risk checks remain valid, and
suggest adding tracked symbols before rerunning. Do not retry automatically.
```

