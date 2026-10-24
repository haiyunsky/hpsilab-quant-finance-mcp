---
name: hpsilab-quant-research
description: Quantitative research on US equities and options with the HPSILab Quant Finance MCP server. Use when the user asks for a stock analysis, implied volatility (IV rank, IV percentile, skew), options positioning (max pain, gamma wall, expected move), a 10-trading-day Monte Carlo price range, a next-trading-day AI prediction, strategy backtests, a pre-trade risk check, or a research report for a US ticker. Research only; never places trades or gives investment advice.
---

# HPSILab Quant Research

This skill tells you when and how to use the HPSILab Quant Finance MCP tools (package version 0.11.1). The server exposes 9 research tools and 1 account tool. Each research tool takes one US-listed stock or ETF ticker per call and returns a JSON object. The tools do not connect to a broker and cannot place, modify, or cancel orders.

## Before you start

Check that the HPSILab tools are available (for example `analyze_stock`, `get_iv_radar`). If they are missing, tell the user to connect the server and stop. Do not invent results.

- Remote endpoint (recommended): `https://hpsilab.com/mcp`, with the header `Authorization: Bearer hpsi_your_key`.
- Local stdio: run `uvx hpsilab-quant-finance-mcp` with the `HPSILAB_API_KEY` environment variable set.
- Every research tool requires a valid API key. A user without one can register at https://hpsilab.com/register and generate a key in Settings, or ask you to register them with `register_account` (see below), which is the only tool that works without a key.

API key rules:

- Never ask the user to paste an API key into the chat.
- Never print, repeat, or summarize a real key, even partly. This includes the `api_key` field returned by `register_account`. Tell the user the key was returned in the tool result and should go into their client's secret configuration as `HPSILAB_API_KEY`.
- Never write a key into files, commands, URLs, or logs. Use `hpsi_your_key` or `${HPSILAB_API_KEY}` as placeholders.

## Choosing a tool

Pass an official uppercase ticker such as `NVDA`, `AAPL`, `SPY`, `QQQ`, or `BRK.B` (pattern `^[A-Z][A-Z0-9.-]{0,15}$`). Convert company names to tickers yourself ("Nvidia" becomes `NVDA`). If the ticker is ambiguous, ask the user.

| The user wants | Call | Parameters (local package) | Credits |
| --- | --- | --- | --- |
| A general view, "analyze X", a bull/bear verdict | `analyze_stock` | `symbol` | 12 |
| Whether options are cheap or expensive, the vol regime, skew | `get_iv_radar` | `symbol` | 3 |
| Max pain, gamma wall, expected move, pressure zones | `get_option_pressure` | `symbol` | 4 |
| A probable price range over the next 10 trading days | `get_monte_carlo` | `symbol` | 5 |
| A model forecast for the next trading day's direction | `get_ai_prediction` | `symbol` | 2 |
| How rule-based strategies performed historically on this ticker | `get_equity_curve` | `symbol` | 6 |
| A risk check before a trade, position sizing, concentration (paid plan; confirm first) | `get_pretrade_risk_scan` | `symbol` | 15 |
| A written report, research note, or deep dive (confirm first) | `generate_stock_research_report` | `symbol` | 30 |
| Charts or visuals (confirm first) | `generate_stock_images` | `symbol`, `force` (default `true`), `types` (optional) | 18 |
| To sign up from here with no key yet, or a fresh key for an existing account, only on explicit request | `register_account` | `email` | none |

Credits are what a signed-in account is charged per call (price version 2026-08-v1; the local package also advertises them as `x-credits` in each tool's metadata). The hosted service is the authority and may change them.

The remote endpoint uses some different parameter names. Always use the names in the tool's own input schema:

- `get_iv_radar`, `get_option_pressure`, `get_monte_carlo`, `get_ai_prediction`, and `get_equity_curve` take `ticker` instead of `symbol`.
- Extra optional parameters on the remote endpoint: `refresh` (`analyze_stock`, `get_iv_radar`, `generate_stock_research_report`), `lang` (`analyze_stock`), and `force_images` (`generate_stock_research_report`). Leave them at their defaults unless the user asks.

### Time horizons: never mix them up

Each tool answers a different horizon. State the horizon whenever you quote a number, and never transfer a number from one horizon to another.

| Tool | Horizon |
| --- | --- |
| `get_ai_prediction` | The **next trading day** only (the next session's direction). |
| `get_monte_carlo` | **10 trading days** ahead (`horizon_days` = 10). |
| `get_option_pressure` | The expiry in `expiry_date`. `expected_move` is for the nearest expiry. |
| `get_iv_radar` | Current IV, ranked against the ticker's history. |
| `get_equity_curve` | Historical backtest. Not a forecast. |
| `get_pretrade_risk_scan` | The forward return distribution covers `methodology.monteCarlo.horizonDays` trading days (10). Responses without `methodology` come from an older service: then do not state a horizon. |

For example, do not describe the AI prediction's `up_probability` as the chance the stock rises over 10 days, and do not describe the Monte Carlo range as tomorrow's range.

### When `analyze_stock` is enough

`analyze_stock` documents only these fields: `signal`, `confidence_score`, `bullish_factors`, `bearish_factors`, `summary`. It does not document separate IV, options, Monte Carlo, prediction, or backtest fields.

- Answer from `analyze_stock` alone only if its response already contains every number the user asked for.
- If the user asks for a specific metric (for example IV rank, max pain, the 90% range, `up_probability`) and it is not in the `analyze_stock` response, call the dedicated tool.
- If the user's question is narrow, call the dedicated tool first and skip `analyze_stock`.
- Do not call the same tool twice for the same ticker in one answer.

Every research call deducts Credits (see the table). Use the fewest calls that fully answer the question. For multiple tickers, call the tool once per ticker, and stop early on the errors listed under [Handling errors](#handling-errors).

## Tools that need confirmation

`generate_stock_research_report` and `generate_stock_images` create hosted artifacts, cost the most Credits (30 and 18), and are not idempotent. Before calling one:

1. Tell the user it creates a hosted artifact and costs Credits.
2. Call it only after the user agrees, or when they explicitly asked for a report or charts.
3. Do not retry automatically after a failure or a timeout. Ask the user first.
4. Do not call it just to get data. Use the read-only tools for that.

`generate_stock_research_report` returns `symbol`, `report` (markdown, about 800–1,200 words in six sections), and `generated_at`. It takes about 10–20 seconds.

`generate_stock_images` defaults to `force: true`, which regenerates images. Pass `force: false` to reuse cached images when the user does not need fresh ones. To limit the work, pass `types` with a subset of `ai_prediction`, `iv_radar`, `option_pressure`, `monte_carlo`, `equity_curves`. The image URLs are public and expire after 24 hours (see `expires_at`), so tell the user. Report the URL fields the response actually contains rather than assuming their names.

`get_pretrade_risk_scan` requires a paid plan (Developer, Team, Enterprise, Pro, or Pro Lifetime) and deducts 15 Credits per call. A Free account is refused with HTTP 403 and is not charged; tell the user the scan needs a paid plan and point them to https://hpsilab.com/pricing. Do not retry, and do not try other accounts. Before calling it, tell the user it costs Credits and call it only after they agree, or when they explicitly asked for a pre-trade risk scan. Call it once per ticker, and do not repeat it for a ticker you already scanned in this conversation. If the balance is too low, the local package returns `insufficient_credits`; the remote endpoint may return `payment_required` with an x402 offer instead. Either way the message states the price and the remaining balance. Relay that, point the user to https://hpsilab.com/pricing, and do not retry. Do not substitute other tools' numbers as a "risk scan".

`register_account` works with or without an API key, on both the local package and the remote endpoint. Without one, it registers a new free account; with one, it returns that caller's account with a fresh key. Either way it sends a verification email. The local package returns JSON with an `api_key` field; the remote endpoint returns text that includes the key. Call it only when the user explicitly asks, with an email address the user gave you; never invent or guess an address. Never call it on your own to get around an error, even when an error's `next_actions` suggests it. After it succeeds, tell the user to: (1) store the returned key as `HPSILAB_API_KEY` in their client's secret configuration, without you repeating it; (2) click the emailed verification link, because the account stays at a capped evaluation allowance with no trial Credits until they do. An address that already belongs to another account is refused; report that and do not retry.

## Reading the results

Field names below are the documented contract in v0.11.1. Live output can change between calls, and some fields can be null or missing for a ticker. When a field is missing, say it is unavailable. Do not estimate a replacement.

Every successful response includes `status: "success"` and a `disclaimer`.

**`get_ai_prediction` (next trading day)**
- `prediction`: `"Up"`, `"Down"`, or `"Neutral"`.
- `up_probability`: 0–1 probability of an up close next session. `confidence`: 0–1 ensemble agreement.
- `model_votes`, `regime` (`"Bull"`, `"Bear"`, `"Chop"`), `signal_strength` (`"Strong"`, `"Moderate"`, `"Weak"`).
- Model accuracy varies by ticker.

**`get_monte_carlo` (10 trading days)**
- 5,000 Geometric Brownian Motion paths, calibrated on historical daily log-return drift and volatility. Not implied volatility.
- The ticker field is `ticker`, not `symbol`.
- `lower_bound` and `upper_bound`: the central range at confidence `ci` (0.90). `mean_price`, `median_price`.
- `support`: 20-day rolling low. `resistance` (also returned as `threshold`): 20-day rolling high.
- `prob_above`: probability (0–1) the price at day 10 is above `resistance`. `prob_below` = 1 − `prob_above`.
- `volatility`: daily log-return standard deviation. `std_tomorrow`: one-day price standard deviation. `final_prices`: every simulated price; do not paste it in full.

**`get_iv_radar`**
- `atm_iv`: at-the-money IV, annualized %. `iv_rank`: 0–100; 80 or above is expensive, 20 or below is cheap. `iv_percentile`: 0–100.
- `risk_reversal`: 25-delta; positive means call skew, negative means put skew.
- `volatility_regime`: `"Low"`, `"Normal"`, `"Elevated"`, or `"Extreme"`.

**`get_option_pressure`**
- `max_pain`, `gamma_wall`, `squeeze_target` are prices. `expected_move` is ± dollars for the nearest expiry. `expiry_date` is YYYY-MM-DD. `pressure_zones` lists strike and open-interest concentrations.

**`get_equity_curve` (historical)**
- `strategies` is a list. Each item has `name`, `total_return` (0.45 = +45%), `sharpe_ratio`, `sortino_ratio`, `max_drawdown` (negative), `win_rate` (0–1), `pl_ratio`, and `equity_curve`.
- Backtests describe the past. Do not present them as expected future returns.

**`get_pretrade_risk_scan`: benchmark versus portfolio**

This tool mixes two different comparisons. Keep them separate.

1. **Stock versus SPY (not the portfolio):**
   - `riskDeltas` compare the SPY benchmark with the stock on its own. In each item, `beforeValue` is SPY's value (beta is 1.0) and `afterValue` is the stock's value. The field names are historical; neither side is the user's portfolio.
   - Never describe `riskDeltas` as the portfolio's risk before and after the trade. Say, for example, "NVDA's annualized volatility is X% versus SPY's Y%."
   - `sizingChecks` (`"Volatility"`, `"Drawdown Risk"`, `"Market Exposure"`, `"Liquidity"`, each `"pass"`, `"warn"`, or `"fail"`) use the stock's own metrics, not the portfolio. For Liquidity, the service warns below 5,000,000 and fails below 500,000 of 20-day average close × volume in the ticker's quote currency (no FX conversion). Current services state those limits in `detail` and in `methodology.thresholds.turnoverBelow`. Older services print $50M / $5M in `detail` while applying 5,000,000 / 500,000; quote the numeric limits, not that text.
   - `distribution`, `range_90` (5th–95th percentile of forward return, %), `mean`, and `threshold` (the break-even line, 0) describe the stock alone, over `methodology.monteCarlo.horizonDays` trading days.
   - `methodology` states how the scan was computed: the data window, the benchmark, the VaR method (`var.horizonDays` is 1), the simulation (`monteCarlo`), and every check's limits (`thresholds`). Use it to state windows and limits instead of guessing. It is absent from older services.
   - `regime` (`"bull"`, `"bear"`, `"chop"`) and `regimeConfidence` describe the market.
2. **Portfolio (the user's tracked watchlist):**
   - Only `exposure` and `correlation` use the user's holdings. They use the watchlist with an equal-weight proxy (`weightingMethod`, `assumedPositionWeight`), not actual position sizes. Say so.
   - `exposure.bySector` and `exposure.bySymbol` give `currentPct`, `postTradePct`, and `deltaPct`. `concentrationFlag` is `"pass"`, `"warn"`, `"fail"`, or `"unknown"`.
   - `correlation.aggregate` gives `avgCorrelationWithPortfolio`, `level`, `mostCorrelated`, and `leastCorrelated`. `correlation.matrix` gives pairwise values.
   - When `available` is false in either section, its data is empty or null. Relay the `reason` text to the user (usually "add symbols to your watchlist"). It is not an error, and you must not fill in portfolio risk yourself.

When signals disagree (for example a bullish `analyze_stock` verdict alongside elevated IV and a low Monte Carlo `prob_above`), report the conflict plainly. Do not pick a side to make the story cleaner.

## Handling errors

Errors return `status: "error"`, an `error_code`, a `message`, and often `status_code` and `next_actions`. A missing key is the exception: it returns `error: "api_key_required"` with `register_url` and `docs_url`. The local package already retries timeouts, server errors, and rate limits for the read-only tools, so do not add your own retry loop.

The error codes, automatic retries, the 60-second Credits circuit, and the 10-requests-per-minute limit below describe the local stdio package. The remote endpoint is a separate service and may word or shape errors differently. When an error does not match this table, follow its `message` and `next_actions`, and apply the same stop rules.

Stop calling HPSILab tools, including for other tickers, when you see `api_key_required`, `insufficient_credits`, `allowance_exhausted`, `settlement_unknown`, or a `status_code` of 401, 402, or 403. Every further call fails the same way.

| `error_code` | What to do |
| --- | --- |
| `api_key_required` (in `error`) | No key is configured. Point the user to https://hpsilab.com/register and the setup steps above. |
| `insufficient_credits` | The key is valid but the Credit balance is empty. `credits_charged` is 0, so nothing was charged. Stop all HPSILab calls. Send the user to the link in `upgrade_url` or in a `next_actions` item's `url`; if none is present, use https://hpsilab.com/pricing. If `circuit_open` is true, calls are blocked locally for `retry_after_seconds`; repeating them does not help. Continue only after the user says they added Credits. |
| `allowance_exhausted` | The free evaluation allowance is used up (`calls_used`, `calls_allowed`). Money does not lift it; registering or verifying the account email does. Show the user the `next_actions` options. If one is `verify_email`, tell the user to click the emailed verification link. If one suggests `register_account`, ask the user before calling it, and use the user's own email. |
| `rate_limited` | Too many requests. The local package allows 10 requests per rolling minute per key. Wait `retry_after_seconds`, then continue with fewer calls. |
| `configuration_error` | The key was rejected (often 401). Further calls with the same key are blocked locally. Ask the user to fix the key in their client configuration and restart the client. |
| `http_error` with `status_code` 401, 402, or 403 | Authentication or authorization failed. Ask the user to check their key and plan. A 403 from `get_pretrade_risk_scan` means the account's plan does not include it; nothing was charged. Do not retry. |
| `payment_required` | The call needs a payment. In the local package this is a real payment challenge, because an out-of-Credits refusal is returned as `insufficient_credits`; the remote endpoint may still use `payment_required` for an out-of-Credits risk scan or report. The `message` states the price and, for Credits, the remaining balance. Stop calling HPSILab tools. Do not pay, configure a wallet, or set up payment, even if the message suggests it. Point the user to https://hpsilab.com/pricing and let them decide. |
| `settlement_unknown` | A payment's outcome is unknown. Never retry, because a retry can pay twice. Give the user the `call_id` if present. |
| `invalid_symbol` | Fix the ticker format and call again once. |
| `invalid_email` | `register_account` needs a real address. Ask the user for one; do not make one up. |
| `request_timeout`, `request_failed`, `invalid_json`, `invalid_response`, other `http_error` | The service did not return usable data. Tell the user. Retry at most once, and never for the artifact tools without asking. |

## How to present results

- Lead with the answer to the user's question, then the supporting numbers with units and horizons. For example: "AI prediction for the next trading day: Up, 0.58 probability" and "Monte Carlo, 10 trading days: 90% range $112–$131."
- Show uncertainty. Use probabilities and ranges, not certainties.
- Do not say a stock "will" go up or down, and do not promise or imply returns.
- Do not tell the user to buy or sell. If they ask what to do, give the research and say the decision is theirs.
- State when the data was produced (for example `asOf` or `generated_at`) when the response includes it.
- End with the `disclaimer` returned by the tool. If none was returned, use: "Research and educational output only. This is not investment advice, financial advice, or a recommendation to buy or sell any security."

## Example requests

- "Analyze SPY and call out any conflicts between the next-day AI prediction, the IV regime, and the 10-day Monte Carlo range."
- "Is TSLA option premium expensive right now? Include IV rank, skew, expected move, and max pain."
- "Run a pre-trade risk check on NVDA against my watchlist."
- "Write a research report on AMD." (Confirm first: this creates a hosted artifact and may use Credits.)
