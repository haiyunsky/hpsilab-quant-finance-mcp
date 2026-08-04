"""Quant Finance MCP Server for Stock Analysis and Options Analytics - HPSILab."""

from importlib.metadata import PackageNotFoundError, version

_FALLBACK_VERSION = "0.8.5+source"


def _load_version() -> str:
    try:
        return version("hpsilab-quant-finance-mcp")
    except PackageNotFoundError:
        # Unpackaged checkout (e.g. running from a plain git clone).
        return _FALLBACK_VERSION


__version__ = _load_version()

__all__ = ["__version__"]
