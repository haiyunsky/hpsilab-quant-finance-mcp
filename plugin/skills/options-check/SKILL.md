---
name: options-check
description: Read the options market for a US stock or ETF. Use when the user asks whether options are cheap or expensive, about implied volatility, IV rank or skew, the expected move into an expiry, max pain, the gamma wall, call or put walls, or where price might be pinned this week.
---

# Options check

Use the HPSILab connector's tools. If they are not available, tell the user to connect HPSILab (https://hpsilab.com/connect) and stop; never invent figures.

1. Get one ticker per call (convert company names yourself; ask if ambiguous).
2. Call `get_iv_radar` for how expensive options are: at-the-money and 30-day implied volatility, IV rank and percentile, the 25-delta risk reversal (skew), the squeeze score and the regime.
3. Call `get_option_pressure` for the nearest weekly or monthly expiry: max pain, the gamma wall, the call and put walls, the weekly expected move, the likely weekly high, the expiry close range and the squeeze target.
4. Present one compact table with the figures, the expiry each one refers to and the data date. Then explain in plain words: what the IV level and rank mean for option prices, which way the skew leans, and which strikes act as support or resistance.
5. If a field comes back unavailable (for example open interest outside market hours), say so and quote the tool's reason instead of estimating it.

These describe how the options market is priced and positioned. They are not a price target or a directional call; say so if the user treats them that way. Do not recommend a trade.
