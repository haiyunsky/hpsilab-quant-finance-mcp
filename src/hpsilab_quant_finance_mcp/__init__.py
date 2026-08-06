"""Quant Finance MCP Server for Stock Analysis and Options Analytics - HPSILab."""

from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

_FALLBACK_VERSION = "0.8.9+source"


def _load_version() -> str:
    # A source checkout can coexist with an older installed distribution.
    # Prefer the checkout marker so stale site-packages metadata cannot make
    # initialization and outbound tracking advertise the wrong release.
    if (Path(__file__).resolve().parents[2] / "pyproject.toml").is_file():
        return _FALLBACK_VERSION
    try:
        return version("hpsilab-quant-finance-mcp")
    except PackageNotFoundError:
        # Unpackaged checkout (e.g. running from a plain git clone).
        return _FALLBACK_VERSION


__version__ = _load_version()

__all__ = ["__version__"]
