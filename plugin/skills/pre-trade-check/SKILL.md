---
name: pre-trade-check
description: Check a stock's risk before buying it. Use when the user is about to buy or add to a US stock or ETF, asks whether a position size is too big, asks how a trade would change their portfolio's risk, or says "should I buy X" and wants the risk side.
---

# Pre-trade risk check

Use the HPSILab connector's tools. If they are not available, tell the user to connect HPSILab (https://hpsilab.com/connect) and stop; never invent figures.

1. **Pin down the trade.** Get the ticker (convert a company name yourself, e.g. "Nvidia" is `NVDA`; ask if it is ambiguous) and the intended size as a share of the portfolio. If the user gives no size, say you will check the default and continue.
2. **Run the check.** Call `get_pretrade_risk_scan` with the ticker. It is a paid-plan tool and spends the user's Credits, so if the user only asked a general question, confirm before calling it. If it is refused for the plan or for Credits, pass on the reason and the link the tool returned, and stop.
3. **Report what came back, in this order:**
   - the overall result and each check marked pass, warn or fail, quoting the rule the tool gives for every warn or fail;
   - the stock's risk range and how it compares with SPY, stating the horizon in trading days that the response gives;
   - sector exposure and correlation with the user's holdings (or watchlist), if present;
   - the data date.
4. **Add options context only if it helps the decision**, for example a warn on volatility: call `get_option_pressure` for the nearest expiry's expected move and walls, or `get_iv_radar` for how expensive options are. Keep each number with its own horizon; never carry a figure from one tool to another's horizon.
5. **Close with the risk picture, not a recommendation.** Say which checks would need to change for the trade to pass (for example a smaller size). Do not tell the user to buy or sell, and do not present any range as a forecast or a guarantee.

The check is saved to the user's history on hpsilab.com, where they can reopen it under the watchlist. Never ask for, print or store an API key.
