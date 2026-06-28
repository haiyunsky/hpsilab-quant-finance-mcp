"""
HPSILab MCP Server
==================
Exposes 8 institutional-grade quantitative finance tools for AI agents.

Authentication
--------------
Set the HPSILAB_API_KEY environment variable to a valid HPSILab API key
(format: hpsi_...).  Free-tier keys have access to a limited set of
tickers; Pro / Team keys unlock the full universe.

Remote endpoint: https://hpsilab.com/mcp
"""

import os
import re
from typing import Any

import requests
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

BASE_URL = "https://hpsilab.com/api"
TIMEOUT = 30
DISCLAIMER = (
    "Research and educational output only. This is not investment advice, "
    "financial advice, or a recommendation to buy or sell any security."
)
SYMBOL_PATTERN = re.compile(r"^[A-Z][A-Z0-9.-]{0,15}$")

mcp = FastMCP("HPSILab MCP Server")


# ── shared helper ──────────────────────────────────────────────────────────────

def _error(
    error_code: str,
    message: str,
    *,
    status_code: int | None = None,
    symbol: str | None = None,
    details: Any | None = None,
) -> dict:
    """Return a consistent error payload for MCP clients."""
    payload: dict[str, Any] = {
        "status": "error",
        "error_code": error_code,
        "message": message,
        "disclaimer": DISCLAIMER,
    }
    if status_code is not None:
        payload["status_code"] = status_code
    if symbol is not None:
        payload["symbol"] = symbol
    if details is not None:
        payload["details"] = details
    return payload


def _get_api_key() -> str:
    return os.getenv("HPSILAB_API_KEY", "").strip()


def _normalize_symbol(symbol: str) -> str:
    if not isinstance(symbol, str):
        raise ValueError("symbol must be a ticker string, such as 'NVDA' or 'SPY'.")

    normalized = symbol.strip().upper()
    if not SYMBOL_PATTERN.fullmatch(normalized):
        raise ValueError(
            "symbol must be an exchange ticker using letters, numbers, '.', or '-', "
            "for example 'NVDA', 'SPY', or 'BRK.B'."
        )
    return normalized


def _message_from_response(response: requests.Response) -> str:
    try:
        payload = response.json()
    except ValueError:
        return response.text[:500] or response.reason

    if isinstance(payload, dict):
        for key in ("message", "error", "detail"):
            value = payload.get(key)
            if isinstance(value, str) and value:
                return value
        return str(payload)

    return str(payload)


def _get(path: str, *, symbol: str | None = None, params: dict | None = None) -> dict:
    """Make an authenticated GET request to the HPSILab API."""
    api_key = _get_api_key()
    if not api_key:
        return _error(
            "missing_api_key",
            "Set HPSILAB_API_KEY to a valid HPSILab API key before calling this tool.",
            symbol=symbol,
        )

    try:
        response = requests.get(
            f"{BASE_URL}/{path}",
            headers={"Authorization": f"Bearer {api_key}"},
            params=params or {},
            timeout=TIMEOUT,
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as exc:
        response = exc.response
        status_code = response.status_code if response is not None else None
        message = _message_from_response(response) if response is not None else str(exc)
        return _error(
            "http_error",
            message,
            status_code=status_code,
            symbol=symbol,
        )
    except requests.exceptions.Timeout:
        return _error(
            "request_timeout",
            f"HPSILab API request timed out after {TIMEOUT} seconds.",
            symbol=symbol,
        )
    except requests.exceptions.RequestException as exc:
        return _error("request_failed", str(exc), symbol=symbol)
    except ValueError as exc:
        return _error("invalid_json", f"HPSILab API returned invalid JSON: {exc}", symbol=symbol)


def _get_symbol_endpoint(endpoint: str, symbol: str) -> dict:
    try:
        normalized_symbol = _normalize_symbol(symbol)
    except ValueError as exc:
        return _error("invalid_symbol", str(exc))

    return _get(f"{endpoint}/{normalized_symbol}", symbol=normalized_symbol)


# ── Tool 1 — comprehensive analysis ───────────────────────────────────────────

@mcp.tool()
def analyze_stock(symbol: str) -> dict:
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

    Parameters
    ----------
    symbol : str
        Exchange ticker in uppercase, e.g. "NVDA", "AAPL", "SPY", "QQQ".
        Do NOT pass company names ("Nvidia") — use official tickers only.

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
    - Free-tier keys are limited to a predefined ticker set.
    - Response latency is ~5–15 s due to multi-model aggregation.
    """
    return _get_symbol_endpoint("analyze_stock", symbol)


# ── Tool 2 — IV radar ─────────────────────────────────────────────────────────

@mcp.tool()
def get_iv_radar(symbol: str) -> dict:
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

    Parameters
    ----------
    symbol : str
        Exchange ticker in uppercase, e.g. "TSLA", "NVDA", "IWM".

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
    return _get_symbol_endpoint("iv_radar", symbol)


# ── Tool 3 — option pressure ──────────────────────────────────────────────────

@mcp.tool()
def get_option_pressure(symbol: str) -> dict:
    """
    Retrieve options-market positioning and dealer-hedging pressure zones.

    Use this tool when:
    - You want to identify max-pain price (where option sellers face least loss
      at expiry) as a gravitational target near expiration.
    - You need to locate gamma walls (strike clusters with large open interest)
      that act as price magnets or resistance/support levels.
    - You want the expected-move range implied by the options market for the
      current weekly/monthly expiry cycle.

    Parameters
    ----------
    symbol : str
        Exchange ticker in uppercase, e.g. "AAPL", "SPY", "NVDA".

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
    return _get_symbol_endpoint("option_pressure", symbol)


# ── Tool 4 — Monte Carlo ──────────────────────────────────────────────────────

@mcp.tool()
def get_monte_carlo(symbol: str) -> dict:
    """
    Run a Monte Carlo price-path simulation for a stock over a 30-day horizon.

    Use this tool when:
    - You need a probabilistic price range rather than a single point estimate.
    - You want to quantify downside risk (e.g., probability of a 10 % drawdown).
    - You are sizing a position using a volatility-adjusted scenario.

    The simulation uses a GBM (Geometric Brownian Motion) model calibrated with
    the stock's realized volatility and current IV.  10,000 paths are run by
    default.

    Parameters
    ----------
    symbol : str
        Exchange ticker in uppercase, e.g. "MSFT", "NVDA", "SPY".

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
    return _get_symbol_endpoint("monte_carlo", symbol)


# ── Tool 5 — AI prediction ────────────────────────────────────────────────────

@mcp.tool()
def get_ai_prediction(symbol: str) -> dict:
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

    Parameters
    ----------
    symbol : str
        Exchange ticker in uppercase, e.g. "NVDA", "META", "QQQ".
        Per-ticker model accuracy varies; META and QQQ have shown above-
        baseline hit rates in backtests.

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
    return _get_symbol_endpoint("ai_prediction", symbol)


# ── Tool 6 — equity curves ────────────────────────────────────────────────────

@mcp.tool()
def get_equity_curves(symbol: str) -> dict:
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

    Parameters
    ----------
    symbol : str
        Exchange ticker in uppercase, e.g. "NVDA", "AAPL", "SPY".

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
    return _get_symbol_endpoint("equity_curves", symbol)


# ── Tool 7 — stock research report ───────────────────────────────────────────

@mcp.tool()
def generate_stock_research_report(symbol: str) -> dict:
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

    Parameters
    ----------
    symbol : str
        Exchange ticker in uppercase, e.g. "NVDA", "TSLA", "SPY".
        Do NOT pass company names — use official tickers only.

    Returns
    -------
    dict with keys:
        symbol       : str — normalized ticker
        report       : str — full markdown report (~800–1200 words, 6 sections)
        generated_at : str — ISO 8601 generation timestamp

    Notes
    -----
    - Requires a valid HPSILAB_API_KEY.
    - Free-tier keys are limited to a predefined ticker set.
    - For programmatic use, prefer analyze_stock which returns structured JSON.
    """
    return _get_symbol_endpoint("stock_research_report", symbol)


# ── Tool 8 — stock chart images ───────────────────────────────────────────────

@mcp.tool()
def generate_stock_images(symbol: str) -> dict:
    """
    Generate chart image URLs for a stock: price chart, IV surface, and
    options flow heatmap.

    Use this tool when:
    - A user explicitly asks to "see", "show", or "visualize" a chart.
    - You want to accompany a written analysis with supporting visuals.
    - You need to share chart links in a report or message.

    Note: Images are served as public URLs.  They expire after 24 hours.
    If images do not render in your client, copy the URL and open it in a
    browser directly.

    Parameters
    ----------
    symbol : str
        Exchange ticker in uppercase, e.g. "NVDA", "AAPL".

    Returns
    -------
    dict with keys:
        symbol          : str — normalized ticker
        price_chart_url : str — URL to candlestick + volume chart (PNG)
        iv_surface_url  : str — URL to 3-D IV surface chart (PNG)
        options_flow_url: str — URL to options flow heatmap (PNG)
        expires_at      : str — ISO 8601 expiry timestamp for the URLs
    """
    return _get_symbol_endpoint("stock_images", symbol)


# ── entry point ────────────────────────────────────────────────────────────────

def main():
    load_dotenv()
    mcp.run()


if __name__ == "__main__":
    main()
