"""
Quant Finance MCP Server for Stock Analysis and Options Analytics - HPSILab
============================================================================
Exposes 9 institutional-grade quantitative finance tools for AI agents.

Authentication
--------------
Set the HPSILAB_API_KEY environment variable to a valid HPSILab API key
(format: hpsi_...).  This server registers the full 9-tool surface; the
hosted API may enforce account-level quotas, rate limits, and symbol coverage.

Remote endpoint: https://hpsilab.com/mcp

Transport
---------
This package calls the hosted REST API through the `hpsilab-mcp` SDK
(https://pypi.org/project/hpsilab-mcp/), which is the single source of truth
for endpoint paths/methods. Keep this file's tool surface in sync with the
SDK's `HpsiMcpClient` rather than re-deriving REST paths here.
"""

import argparse
import json
import os
from typing import Annotated, Any, Literal

from dotenv import load_dotenv
from mcp import types
from mcp.server.fastmcp import FastMCP
from pydantic import Field

from . import __version__
from .service import DISCLAIMER as SERVICE_DISCLAIMER
from .service import QuantFinanceService, error_payload, normalize_symbol

DISCLAIMER = SERVICE_DISCLAIMER

READ_ONLY_ANNOTATIONS = {
    "readOnlyHint": True,
    "destructiveHint": False,
    "idempotentHint": True,
    "openWorldHint": True,
}

# These tools create externally hosted chart/report artifacts and can consume
# metered quota. They do not overwrite or delete existing resources, but
# repeated calls can create or charge again and therefore are not idempotent.
CREATE_EXTERNAL_ARTIFACT_ANNOTATIONS = {
    "readOnlyHint": False,
    "destructiveHint": False,
    "idempotentHint": False,
    "openWorldHint": True,
}


class ProtocolFastMCP(FastMCP):
    """FastMCP adapter that preserves structured errors and marks them as errors."""

    async def call_tool(self, name: str, arguments: dict[str, Any]):
        result = await super().call_tool(name, arguments)
        structured = result
        if isinstance(result, tuple) and len(result) == 2:
            structured = result[1]
        if isinstance(structured, dict) and structured.get("status") == "error":
            return types.CallToolResult(
                content=[types.TextContent(type="text", text=json.dumps(structured, indent=2))],
                structuredContent=structured,
                isError=True,
            )
        return result


mcp = ProtocolFastMCP(
    "Quant Finance MCP Server for Stock Analysis and Options Analytics - HPSILab",
    instructions=(
        "Quantitative stock and options research only; never execute trades. "
        "Use analyze_stock for a broad overview and dedicated tools for IV, options pressure, "
        "Monte Carlo, backtests, or pre-trade risk. Live market outputs can change. "
        "generate_stock_images and generate_stock_research_report create hosted artifacts, "
        "may consume quota, and are not idempotent."
    ),
    website_url="https://hpsilab.com",
    json_response=True,
)
# FastMCP 1.27 otherwise falls back to advertising the MCP Python SDK version
# in initialize.serverInfo instead of this package's release version.
mcp._mcp_server.version = __version__

StockReportImageType = Literal[
    "ai_prediction",
    "iv_radar",
    "option_pressure",
    "monte_carlo",
    "equity_curves",
]


# ── shared service adapter ─────────────────────────────────────────────────────

_service = QuantFinanceService()


def _error(*args: Any, **kwargs: Any) -> dict[str, Any]:
    """Backward-compatible alias for the historical private helper."""
    return error_payload(*args, **kwargs)


def _get_api_key() -> str:
    """Backward-compatible helper used by downstream diagnostics."""
    return os.getenv("HPSILAB_API_KEY", "").strip()


def _normalize_symbol(symbol: str) -> str:
    """Backward-compatible alias for the shared service validator."""
    return normalize_symbol(symbol)


def _call(method_name: str, symbol: str, **kwargs: Any) -> dict[str, Any]:
    return _service.call(method_name, symbol, **kwargs)


_TICKER_FIELD = Field(
    description=(
        "Exchange ticker in uppercase, e.g. 'NVDA', 'AAPL', 'SPY', 'QQQ'. "
        "Do NOT pass company names ('Nvidia') — use official tickers only."
    ),
    pattern=r"^[A-Z][A-Z0-9.-]{0,15}$",
    examples=["NVDA", "AAPL", "SPY", "QQQ"],
)


# ── Tool 1 — comprehensive analysis ───────────────────────────────────────────


@mcp.tool(annotations=READ_ONLY_ANNOTATIONS, meta={"x-tier": "free"})
def analyze_stock(symbol: Annotated[str, _TICKER_FIELD]) -> dict[str, Any]:
    """
    Run a full institutional-grade quantitative analysis for a single stock.

    This is the **primary tool** for a complete market view.  It aggregates
    results from AI prediction, implied-volatility radar, options-pressure map,
    Monte Carlo simulation, and strategy backtesting into one unified signal.

    Use this tool when:
    - You need a holistic bull/bear verdict with supporting evidence.
    - You want to compare multiple signal sources in a single call.
    - A user asks for a "stock analysis", "market view", or "trading signal".

    Prefer the dedicated sub-tools (get_iv_radar, get_monte_carlo, etc.) when
    you need only a specific data dimension, to reduce latency and token usage.

    Returns
    -------
    dict with keys:
        symbol          : str   — normalized ticker
        signal          : str   — "Bullish" | "Bearish" | "Neutral"
        confidence_score: int   — 0–100 directional confidence
        bullish_factors : list  — evidence supporting an upward move
        bearish_factors : list  — evidence supporting a downward move
        summary         : str   — one-sentence synthesis

    Notes
    -----
    - Requires a valid HPSILAB_API_KEY.
    - API access, quota, and ticker coverage are governed by the HPSILab account.
    - Response latency is ~5–15 s due to multi-model aggregation.
    """
    return _call("analyze_stock", symbol)


# ── Tool 2 — IV radar ─────────────────────────────────────────────────────────


@mcp.tool(annotations=READ_ONLY_ANNOTATIONS, meta={"x-tier": "free"})
def get_iv_radar(symbol: Annotated[str, _TICKER_FIELD]) -> dict[str, Any]:
    """
    Retrieve implied-volatility (IV) metrics for a single stock.

    Use this tool when:
    - You need to assess whether options are cheap or expensive relative to
      historical norms (IV rank / IV percentile).
    - You want the current volatility regime ("Low", "Normal", "Elevated",
      "Extreme") to frame risk sizing or strategy selection.
    - You are analyzing skew or risk-reversal direction (put-heavy vs
      call-heavy market).

    Do NOT use this tool if you already called analyze_stock — the IV data is
    included in that response.

    Returns
    -------
    dict with keys:
        symbol          : str   — normalized ticker
        atm_iv          : float — at-the-money implied volatility (annualized %)
        iv_rank         : float — 0–100; ≥80 = expensive, ≤20 = cheap
        iv_percentile   : float — historical percentile (0–100)
        risk_reversal   : float — 25-delta risk reversal (positive = call-skew)
        volatility_regime: str  — "Low" | "Normal" | "Elevated" | "Extreme"
    """
    return _call("get_iv_radar", symbol)


# ── Tool 3 — option pressure ──────────────────────────────────────────────────


@mcp.tool(annotations=READ_ONLY_ANNOTATIONS, meta={"x-tier": "free"})
def get_option_pressure(symbol: Annotated[str, _TICKER_FIELD]) -> dict[str, Any]:
    """
    Retrieve options-market positioning and dealer-hedging pressure zones.

    Use this tool when:
    - You want to identify max-pain price (where option sellers face least loss
      at expiry) as a gravitational target near expiration.
    - You need to locate gamma walls (strike clusters with large open interest)
      that act as price magnets or resistance/support levels.
    - You want the expected-move range implied by the options market for the
      current weekly/monthly expiry cycle.

    Returns
    -------
    dict with keys:
        symbol        : str   — normalized ticker
        max_pain      : float — max-pain strike price
        gamma_wall    : float — largest gamma concentration strike
        expected_move : float — ±expected move in dollars for nearest expiry
        squeeze_target: float — upside squeeze price target
        expiry_date   : str   — target expiry date (YYYY-MM-DD)
        pressure_zones: list  — list of significant strike/OI concentration dicts
    """
    return _call("get_option_pressure", symbol)


# ── Tool 4 — Monte Carlo ──────────────────────────────────────────────────────


@mcp.tool(annotations=READ_ONLY_ANNOTATIONS, meta={"x-tier": "free"})
def get_monte_carlo(symbol: Annotated[str, _TICKER_FIELD]) -> dict[str, Any]:
    """
    Run a Monte Carlo price-path simulation for a stock over a 30-day horizon.

    Use this tool when:
    - You need a probabilistic price range rather than a single point estimate.
    - You want to quantify downside risk (e.g., probability of a 10 % drawdown).
    - You are sizing a position using a volatility-adjusted scenario.

    The simulation uses a GBM (Geometric Brownian Motion) model calibrated with
    the stock's realized volatility and current IV.  10,000 paths are run by
    default.

    Returns
    -------
    dict with keys:
        symbol         : str   — normalized ticker
        current_price  : float — spot price at simulation start
        mean_price     : float — expected price at horizon
        range_90       : dict  — {"lower": float, "upper": float} 90 % CI
        range_68       : dict  — {"lower": float, "upper": float} 68 % CI
        prob_above_spot: float — probability (0–1) price is above current spot
        prob_10pct_drop: float — probability (0–1) of ≥10 % decline
        distribution   : dict  — histogram data:
                                 {"bins": list, "frequencies": list,
                                  "kde_x": list, "kde_y": list}
    """
    return _call("get_monte_carlo", symbol)


# ── Tool 5 — AI prediction ────────────────────────────────────────────────────


@mcp.tool(annotations=READ_ONLY_ANNOTATIONS, meta={"x-tier": "free"})
def get_ai_prediction(
    symbol: Annotated[
        str,
        Field(
            description=(
                "Exchange ticker in uppercase, e.g. 'NVDA', 'META', 'QQQ'. "
                "Do NOT pass company names — use official tickers only. "
                "Per-ticker model accuracy varies; META and QQQ have shown "
                "above-baseline hit rates in backtests."
            ),
            pattern=r"^[A-Z][A-Z0-9.-]{0,15}$",
            examples=["NVDA", "META", "QQQ"],
        ),
    ],
) -> dict[str, Any]:
    """
    Get an AI/ML directional prediction for a stock's next-session move.

    Use this tool when:
    - You want a data-driven probability estimate for the next trading day's
      direction (up vs. down).
    - You need the individual model votes (ensemble breakdown) to assess
      consensus strength.
    - You want to compare model confidence against current IV pricing.

    The prediction engine uses an ensemble of gradient-boosted trees, an LSTM,
    and a VQC (quantum-classical hybrid) model.  Features include VIX, relative
    strength, Treasury rates, and options flow signals.

    Returns
    -------
    dict with keys:
        symbol          : str   — normalized ticker
        prediction      : str   — "Up" | "Down" | "Neutral"
        up_probability  : float — 0.0–1.0 probability of upward close
        confidence      : float — 0.0–1.0 ensemble agreement score
        model_votes     : dict  — per-model predictions and probabilities
        regime          : str   — "Bull" | "Bear" | "Chop" market regime
        signal_strength : str   — "Strong" | "Moderate" | "Weak"
    """
    return _call("get_ai_prediction", symbol)


# ── Tool 6 — equity curves ────────────────────────────────────────────────────


@mcp.tool(annotations=READ_ONLY_ANNOTATIONS, meta={"x-tier": "free"})
def get_equity_curves(symbol: Annotated[str, _TICKER_FIELD]) -> dict[str, Any]:
    """
    Retrieve backtested equity curves and performance metrics for standard
    quantitative strategies applied to a single stock.

    Use this tool when:
    - You want to evaluate how well rule-based strategies (momentum, mean-
      reversion, vol-targeting) have performed on this specific ticker.
    - You need risk-adjusted return metrics (Sharpe, Sortino, max drawdown)
      to compare strategy quality.
    - You are building a multi-leg options strategy and want historical
      context for the underlying's trending vs. mean-reverting behavior.

    Returns
    -------
    dict with keys:
        symbol      : str  — normalized ticker
        strategies  : list — each item is a dict with:
            name          : str   — strategy name
            total_return  : float — cumulative return (e.g., 0.45 = +45 %)
            sharpe_ratio  : float — annualized Sharpe ratio
            sortino_ratio : float — annualized Sortino ratio
            max_drawdown  : float — maximum peak-to-trough loss (negative)
            win_rate      : float — fraction of winning trades (0–1)
            pl_ratio      : float — average win / average loss
            equity_curve  : list  — daily portfolio value series
    """
    return _call("get_equity_curves", symbol)


# ── Tool 7 — stock research report ───────────────────────────────────────────


@mcp.tool(
    annotations=CREATE_EXTERNAL_ARTIFACT_ANNOTATIONS,
    meta={
        "x-tier": "pro",
        "x-access": {
            "signed_in": "free",
            "anonymous": {"payment": "x402", "amount_usdc": 0.35},
        },
    },
)
def generate_stock_research_report(
    symbol: Annotated[
        str,
        Field(
            description=(
                "Exchange ticker in uppercase, e.g. 'NVDA', 'TSLA', 'SPY'. "
                "Do NOT pass company names — use official tickers only."
            ),
            pattern=r"^[A-Z][A-Z0-9.-]{0,15}$",
            examples=["NVDA", "TSLA", "SPY"],
        ),
    ],
) -> dict[str, Any]:
    """
    Generate a structured, institutional-style markdown research report for
    a single stock, covering all major quantitative signal sources.

    The report is divided into six sections:
      1. Executive Summary   — bull/bear verdict, confidence score, one-line thesis
      2. AI Prediction       — ensemble model votes, up-probability, regime
      3. Volatility Analysis — ATM IV, IV rank, vol regime, risk reversal
      4. Options Positioning — max pain, gamma wall, expected move, squeeze targets
      5. Monte Carlo Outlook — 30-day price distribution, 90 %/68 % confidence ranges
      6. Strategy Backtests  — Sharpe, max drawdown, win rate across quant strategies

    Output is a complete markdown string (~800–1200 words) ready to render or share.
    Response latency is ~10–20 s due to full multi-model data aggregation.

    Use this tool when:
    - A user asks for a "report", "write-up", "research note", or "deep dive".
    - You want a pre-formatted narrative combining all signal sources in one document.
    - You need output suitable for archiving, PDF export, or investor communication.

    Do NOT use this tool when:
    - You only need a quick directional verdict → use analyze_stock instead.
    - You need a specific data dimension (IV, Monte Carlo, etc.) → use the
      dedicated sub-tool (get_iv_radar, get_monte_carlo, etc.) for lower latency.

    Returns
    -------
    dict with keys:
        symbol       : str — normalized ticker
        report       : str — full markdown report (~800–1200 words, 6 sections)
        generated_at : str — ISO 8601 generation timestamp

    Notes
    -----
    - Requires a valid HPSILAB_API_KEY.
    - API access, quota, and ticker coverage are governed by the HPSILab account.
    - For programmatic use, prefer analyze_stock which returns structured JSON.
    """
    return _call("generate_stock_research_report", symbol)


# ── Tool 8 — stock chart images ───────────────────────────────────────────────


@mcp.tool(
    annotations=CREATE_EXTERNAL_ARTIFACT_ANNOTATIONS,
    meta={"x-tier": "free"},
)
def generate_stock_images(
    symbol: Annotated[
        str,
        Field(
            description=(
                "Exchange ticker in uppercase, e.g. 'NVDA', 'AAPL'. "
                "Do NOT pass company names — use official tickers only."
            ),
            pattern=r"^[A-Z][A-Z0-9.-]{0,15}$",
            examples=["NVDA", "AAPL"],
        ),
    ],
    force: Annotated[
        bool,
        Field(description="Regenerate hosted images instead of reusing cached artifacts."),
    ] = True,
    types: Annotated[
        list[StockReportImageType] | None,
        Field(description="Optional chart types to generate. Omit or use null to generate every type."),
    ] = None,
) -> dict[str, Any]:
    """
    Generate chart image URLs for a stock: price chart, IV surface, and
    options flow heatmap.

    Use this tool when:
    - A user explicitly asks to "see", "show", or "visualize" a chart.
    - You want to accompany a written analysis with supporting visuals.
    - You need to share chart links in a report or message.

    Parameters
    ----------
    force:
        Regenerate images instead of reusing cached artifacts. Defaults to True.
    types:
        Optional subset of chart types. Allowed values: ai_prediction,
        iv_radar, option_pressure, monte_carlo, equity_curves. Omit to
        generate every chart type.

    Note: Images are served as public URLs.  They expire after 24 hours.
    If images do not render in your client, copy the URL and open it in a
    browser directly.

    Returns
    -------
    dict with keys:
        symbol          : str — normalized ticker
        price_chart_url : str — URL to candlestick + volume chart (PNG)
        iv_surface_url  : str — URL to 3-D IV surface chart (PNG)
        options_flow_url: str — URL to options flow heatmap (PNG)
        expires_at      : str — ISO 8601 expiry timestamp for the URLs
    """
    return _call("generate_stock_images", symbol, force=force, types=types)


# ── Tool 9 — pre-trade risk scan ───────────────────────────────────────────────


@mcp.tool(
    annotations=READ_ONLY_ANNOTATIONS,
    meta={
        "x-tier": "pro",
        "x-access": {
            "signed_in": "free",
            "anonymous": {"payment": "x402", "amount_usdc": 0.15},
        },
    },
)
def get_pretrade_risk_scan(
    symbol: Annotated[
        str,
        Field(
            description=(
                "Exchange ticker in uppercase, e.g. 'NVDA', 'AAPL', 'SPY'. "
                "Do NOT pass company names — use official tickers only."
            ),
            pattern=r"^[A-Z][A-Z0-9.-]{0,15}$",
            examples=["NVDA", "AAPL", "SPY"],
        ),
    ],
) -> dict[str, Any]:
    """
    Run a pre-trade risk scan for adding a single stock to the user's tracked
    portfolio, covering volatility/beta/VaR/drawdown deltas, market regime,
    a forward return distribution, position-sizing checks, sector/symbol
    exposure impact, and correlation against existing holdings.

    Use this tool when:
    - You need a risk-first check before evaluating or placing a trade.
    - You want position-sizing guardrails (volatility, drawdown, beta,
      liquidity) evaluated against warn/fail thresholds, not just raw numbers.
    - You need to see how adding this symbol would shift sector or
      per-symbol concentration in the existing portfolio.
    - You want the new symbol's correlation to current holdings, to judge
      diversification benefit vs. redundant exposure.

    Do NOT use this tool for:
    - A standalone price-distribution simulation with no portfolio context →
      use get_monte_carlo instead.
    - A general bullish/bearish read on the stock → use analyze_stock.

    Example
    -------
    get_pretrade_risk_scan("NVDA")

    Returns
    -------
    dict with keys:
        symbol         : str   — normalized ticker
        asOf           : str   — ISO 8601 date the scan was computed
        regime         : str   — "bull" | "bear" | "chop" market regime
        regimeConfidence: float — 0–1 confidence in the regime classification
        riskDeltas     : list  — before/after risk metrics from adding the
                                  position, each item a dict with:
            label           : str   — e.g. "Annualized Volatility", "Beta (vs SPY)",
                                       "1-Day VaR (95%)", "Max Drawdown (1Y)"
            beforeValue     : float — metric value for current portfolio
            afterValue      : float — metric value after adding the position
            unit            : str   — "%" or "" (unitless, e.g. beta)
            higherIsRiskier : bool  — whether an increase in this metric is worse
        distribution   : dict  — forward return distribution:
                                  {"bins": list, "frequencies": list,
                                   "kde_x": list, "kde_y": list}
        range_90       : dict  — {"lower": float, "upper": float} 90 % CI on
                                  forward return (%)
        mean           : float — expected forward return (%)
        threshold      : float — reference return threshold used in the scan
        sizingChecks   : list  — pass/warn/fail guardrail checks, each a dict:
            label   : str — "Volatility" | "Drawdown Risk" | "Market Exposure"
                            | "Liquidity"
            status  : str — "pass" | "warn" | "fail"
            detail  : str — human-readable explanation with the thresholds used
        exposure       : dict  — portfolio concentration impact:
            available            : bool  — false if the user has no watchlist
                                            symbols to compare against
            bySector             : list of {sector, currentPct, postTradePct, deltaPct}
                                            — empty list when available is false
            bySymbol             : list of {symbol, currentPct, postTradePct, deltaPct}
                                            — empty list when available is false
            concentrationFlag    : str  — "pass" | "warn" | "fail" | "unknown"
                                            ("unknown" when available is false)
            assumedPositionWeight: float | None — None when available is false
            weightingMethod      : str  — e.g. "equal_weight_proxy"
            reason                : str  — present only when available is false;
                                            human-readable explanation (e.g. "No
                                            watchlist symbols to compare against.
                                            Add symbols to your watchlist to see
                                            portfolio exposure.") — surface this
                                            to the user instead of guessing why
                                            the section is empty
        correlation    : dict  — correlation of the new symbol to holdings:
            available : bool  — false if the user has no watchlist symbols to
                                 compare against
            aggregate : dict | None — None when available is false; otherwise
                                 {avgCorrelationWithPortfolio, level,
                                  mostCorrelated: {symbol, correlation},
                                  leastCorrelated: {symbol, correlation}}
            matrix    : dict | None — None when available is false; otherwise
                                 {"symbols": list, "values": list[list[float]]}
                                 full pairwise correlation matrix
            reason    : str  — present only when available is false;
                                 human-readable explanation (e.g. "No watchlist
                                 symbols to compare against. Add symbols to your
                                 watchlist to see correlation.") — surface this
                                 to the user instead of guessing why the section
                                 is empty

    Notes
    -----
    - Requires a valid HPSILAB_API_KEY.
    - Exposure and correlation sections assume the user has an existing
      tracked watchlist/portfolio. If none exists, "available" is false in
      both sections, their data fields are null/empty, and each includes a
      "reason" string explaining why — relay that reason to the user (e.g.
      suggest adding symbols to their watchlist) rather than treating the
      missing data as an error.
    """
    return _call("get_pretrade_risk_scan", symbol)


# ── entry point ────────────────────────────────────────────────────────────────


def create_http_app():
    """Return the ASGI Streamable HTTP application for external hosting."""
    return mcp.streamable_http_app()


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="HPSILab Quant Finance MCP server")
    parser.add_argument(
        "--transport",
        choices=("stdio", "streamable-http"),
        default=os.getenv("HPSILAB_MCP_TRANSPORT", "stdio"),
        help="MCP transport (default: stdio; env: HPSILAB_MCP_TRANSPORT)",
    )
    parser.add_argument(
        "--host",
        default=os.getenv("HPSILAB_MCP_HOST", "127.0.0.1"),
        help="HTTP bind host (default: 127.0.0.1; env: HPSILAB_MCP_HOST)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.getenv("HPSILAB_MCP_PORT", "8000")),
        help="HTTP bind port (default: 8000; env: HPSILAB_MCP_PORT)",
    )
    args = parser.parse_args(argv)
    if args.transport == "streamable-http" and args.host not in {"127.0.0.1", "localhost", "::1"}:
        parser.error(
            "the built-in HTTP runner only binds to loopback; use create_http_app() "
            "with explicit production transport-security settings for remote hosting"
        )
    return args


def main(argv: list[str] | None = None):
    load_dotenv()
    args = _parse_args(argv)
    mcp.settings.host = args.host
    mcp.settings.port = args.port
    mcp.run(transport=args.transport)


if __name__ == "__main__":
    main()
