"""Reusable service adapter shared by every MCP transport."""

from __future__ import annotations

import re
from collections.abc import Callable
from typing import Any, Protocol

from hpsilab_mcp import (
    HpsiMcpAuthError,
    HpsiMcpClient,
    HpsiMcpConnectionError,
    HpsiMcpPaymentError,
    HpsiMcpRateLimitError,
    HpsiMcpResponseError,
    HpsiMcpTimeoutError,
)

from .auth import CredentialProvider, EnvironmentApiKeyProvider

DISCLAIMER = (
    "Research and educational output only. This is not investment advice, "
    "financial advice, or a recommendation to buy or sell any security."
)
SYMBOL_PATTERN = re.compile(r"^[A-Z][A-Z0-9.-]{0,15}$")


class ClientFactory(Protocol):
    """Construct the downstream SDK client."""

    def __call__(self, *, api_key: str) -> HpsiMcpClient: ...


def error_payload(
    error_code: str,
    message: str,
    *,
    status_code: int | None = None,
    symbol: str | None = None,
    details: Any | None = None,
) -> dict[str, Any]:
    """Build the stable, machine-readable error shape used by every tool."""
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


def normalize_symbol(symbol: str) -> str:
    """Normalize and validate an exchange ticker at the service boundary."""
    if not isinstance(symbol, str):
        raise ValueError("symbol must be a ticker string, such as 'NVDA' or 'SPY'.")

    normalized = symbol.strip().upper()
    if not SYMBOL_PATTERN.fullmatch(normalized):
        raise ValueError(
            "symbol must be an exchange ticker using letters, numbers, '.', or '-', "
            "for example 'NVDA', 'SPY', or 'BRK.B'."
        )
    return normalized


def normalize_success_payload(result: dict[str, Any]) -> dict[str, Any]:
    """Add stable envelope fields without changing existing response fields."""
    payload = dict(result)
    payload.setdefault("status", "success")
    payload.setdefault("disclaimer", DISCLAIMER)
    return payload


class QuantFinanceService:
    """Validate input, call the official SDK, and normalize service results."""

    def __init__(
        self,
        credential_provider: CredentialProvider | None = None,
        client_factory: ClientFactory | Callable[..., HpsiMcpClient] = HpsiMcpClient,
    ) -> None:
        self._credential_provider = credential_provider or EnvironmentApiKeyProvider()
        self._client_factory = client_factory

    def call(self, method_name: str, symbol: str, **kwargs: Any) -> dict[str, Any]:
        try:
            normalized_symbol = normalize_symbol(symbol)
        except ValueError as exc:
            return error_payload("invalid_symbol", str(exc))

        api_key = self._credential_provider.get_api_key()
        if not api_key:
            return error_payload(
                "missing_api_key",
                "Set HPSILAB_API_KEY to a valid HPSILab API key before calling this tool.",
                symbol=normalized_symbol,
            )

        try:
            with self._client_factory(api_key=api_key) as client:
                method = getattr(client, method_name)
                result = method(normalized_symbol, **kwargs)
            if not isinstance(result, dict):
                return error_payload(
                    "invalid_response",
                    "The HPSILab service returned a non-object response.",
                    symbol=normalized_symbol,
                )
            return normalize_success_payload(result)
        except HpsiMcpPaymentError as exc:
            return error_payload("payment_required", str(exc), status_code=exc.status_code, symbol=normalized_symbol)
        except HpsiMcpRateLimitError as exc:
            return error_payload("rate_limited", str(exc), status_code=exc.status_code, symbol=normalized_symbol)
        except HpsiMcpAuthError as exc:
            return error_payload("http_error", str(exc), status_code=exc.status_code, symbol=normalized_symbol)
        except HpsiMcpTimeoutError as exc:
            return error_payload("request_timeout", str(exc), symbol=normalized_symbol)
        except HpsiMcpConnectionError as exc:
            return error_payload("request_failed", str(exc), symbol=normalized_symbol)
        except HpsiMcpResponseError as exc:
            return error_payload("invalid_json", str(exc), status_code=exc.status_code, symbol=normalized_symbol)
        except Exception as exc:
            status_code = getattr(exc, "status_code", None)
            return error_payload("http_error", str(exc), status_code=status_code, symbol=normalized_symbol)
