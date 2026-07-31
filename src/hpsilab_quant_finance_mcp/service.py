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
            # Name the way out, in the caller's own terms. Without this the
            # message is a dead end: the caller is told it needs a credential
            # it has no way to obtain, while the tool that hands one over sits
            # unmentioned in the same tool list.
            return error_payload(
                "missing_api_key",
                "No API key configured. If you do not have one, call the register_account "
                "tool with an email address to create a free account and receive a key - "
                "no password, wallet, or web form needed. Then set HPSILAB_API_KEY to the "
                "returned api_key. If you already have a key, set HPSILAB_API_KEY to it.",
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

    def register_account(self, email: str) -> dict[str, Any]:
        """Create a free HPSILab account for the caller and return an API key.

        Deliberately does not go through `call()`. That path validates a ticker
        and refuses outright when HPSILAB_API_KEY is unset — both correct for a
        market-data tool and both wrong here. This is the one operation whose
        entire purpose is to serve a caller that has **no** key yet, so
        requiring one would make it unreachable exactly when it is needed.

        An existing key is still passed through when present: the SDK then
        leaves it in place rather than swapping the caller's credential, and
        the backend answers idempotently for a caller that is already
        registered.
        """
        normalized_email = (email or "").strip()
        if "@" not in normalized_email or len(normalized_email) < 3:
            return error_payload(
                "invalid_email",
                "email must be a real address, for example 'you@example.com'. "
                "The verification link is sent there, and an address nobody "
                "reads leaves the account at the anonymous allowance.",
            )

        try:
            with self._client_factory(api_key=self._credential_provider.get_api_key()) as client:
                result = client.register_account(normalized_email)
            if not isinstance(result, dict):
                return error_payload(
                    "invalid_response",
                    "The HPSILab service returned a non-object response.",
                )
            return normalize_success_payload(result)
        except HpsiMcpAuthError as exc:
            return error_payload("http_error", str(exc), status_code=exc.status_code)
        except HpsiMcpRateLimitError as exc:
            return error_payload("rate_limited", str(exc), status_code=exc.status_code)
        except HpsiMcpTimeoutError as exc:
            return error_payload("request_timeout", str(exc))
        except HpsiMcpConnectionError as exc:
            return error_payload("request_failed", str(exc))
        except HpsiMcpResponseError as exc:
            return error_payload("invalid_json", str(exc), status_code=exc.status_code)
        except Exception as exc:
            # A 409 lands here: the address already belongs to a different
            # account. Surfaced as-is rather than retried or rewritten — an
            # agent must not be able to attach itself to someone else's account.
            status_code = getattr(exc, "status_code", None)
            return error_payload("http_error", str(exc), status_code=status_code)
