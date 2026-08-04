"""Reusable service adapter shared by every MCP transport."""

from __future__ import annotations

import json
import re
import time
from collections.abc import Callable
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any, Protocol

import httpx
from hpsilab_mcp import (
    HpsiMcpAPIError,
    HpsiMcpAuthError,
    HpsiMcpClient,
    HpsiMcpConnectionError,
    HpsiMcpPaymentError,
    HpsiMcpRateLimitError,
    HpsiMcpResponseError,
    HpsiMcpTimeoutError,
)
from hpsilab_mcp import register as hpsilab_register

from . import __version__
from .auth import CredentialProvider, EnvironmentApiKeyProvider

DISCLAIMER = (
    "Research and educational output only. This is not investment advice, "
    "financial advice, or a recommendation to buy or sell any security."
)
SYMBOL_PATTERN = re.compile(r"^[A-Z][A-Z0-9.-]{0,15}$")
REGISTER_URL = "https://hpsilab.com/register"
DOCS_URL = "https://hpsilab.com/developer/v2"
DEFAULT_MAX_RETRIES = 2
USER_AGENT = f"hpsilab-python-sdk/{__version__}"
RETRYABLE_STATUS_CODES = frozenset({500, 502, 503, 504})
RETRYABLE_METHODS = frozenset(
    {
        "analyze_stock",
        "get_ai_prediction",
        "get_iv_radar",
        "get_option_pressure",
        "get_pretrade_risk_scan",
        "get_monte_carlo",
        "get_equity_curve",
    }
)


class QuantFinanceClient(HpsiMcpClient):
    """Preserve Retry-After metadata exposed by the downstream response."""

    def _raise_for_status(self, response: httpx.Response) -> None:
        try:
            super()._raise_for_status(response)
        except HpsiMcpRateLimitError as exc:
            exc.response_headers = response.headers
            raise


class ClientFactory(Protocol):
    """Construct the downstream SDK client."""

    def __call__(self, *, api_key: str, headers: dict[str, str]) -> HpsiMcpClient: ...


class RegisterFn(Protocol):
    """Bootstrap a free account with no client instance and no prior identity."""

    def __call__(self, *, email: str) -> dict[str, Any]: ...


def api_key_required_payload() -> dict[str, str]:
    """Return the exact local error contract without contacting the API."""
    return {
        "error": "api_key_required",
        "message": "A free API key is required.",
        "register_url": REGISTER_URL,
        "docs_url": DOCS_URL,
    }


def retry_after_seconds(exc: BaseException) -> float | None:
    """Read Retry-After from structured SDK error data when available."""
    headers = getattr(exc, "response_headers", None)
    value: Any = headers.get("Retry-After") if hasattr(headers, "get") else None
    if value is None:
        body = getattr(exc, "body", None)
        if isinstance(body, dict):
            value = body.get("retry_after") or body.get("retry_after_seconds")
    if value is None:
        return None
    try:
        return max(0.0, float(value))
    except (TypeError, ValueError):
        if not isinstance(value, str):
            return None
        try:
            retry_at = parsedate_to_datetime(value)
        except (TypeError, ValueError, OverflowError):
            return None
        if retry_at.tzinfo is None:
            retry_at = retry_at.replace(tzinfo=timezone.utc)
        return max(0.0, (retry_at - datetime.now(timezone.utc)).total_seconds())


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


def normalize_ai_prediction_result(result: Any) -> dict[str, Any] | None:
    """Convert supported SDK prediction responses to a plain dictionary."""
    if isinstance(result, dict):
        return result
    if isinstance(result, list):
        if len(result) != 1:
            return None
        return normalize_ai_prediction_result(result[0])
    if isinstance(result, str):
        try:
            decoded = json.loads(result)
        except (TypeError, ValueError):
            return None
        return normalize_ai_prediction_result(decoded)
    model_dump = getattr(result, "model_dump", None)
    if callable(model_dump):
        decoded = model_dump()
        return normalize_ai_prediction_result(decoded)
    return None


class QuantFinanceService:
    """Validate input, call the official SDK, and normalize service results."""

    def __init__(
        self,
        credential_provider: CredentialProvider | None = None,
        client_factory: ClientFactory | Callable[..., HpsiMcpClient] = QuantFinanceClient,
        register_fn: RegisterFn | Callable[..., dict[str, Any]] = hpsilab_register,
        max_retries: int = DEFAULT_MAX_RETRIES,
        sleep_fn: Callable[[float], None] = time.sleep,
    ) -> None:
        if not isinstance(max_retries, int) or isinstance(max_retries, bool) or max_retries < 0:
            raise ValueError("max_retries must be a non-negative integer.")
        self._credential_provider = credential_provider or EnvironmentApiKeyProvider()
        self._client_factory = client_factory
        self._register_fn = register_fn
        self._max_retries = max_retries
        self._sleep = sleep_fn

    def call(self, method_name: str, symbol: str, **kwargs: Any) -> dict[str, Any]:
        api_key = self._credential_provider.get_api_key()
        if not api_key:
            return api_key_required_payload()

        try:
            normalized_symbol = normalize_symbol(symbol)
        except ValueError as exc:
            return error_payload("invalid_symbol", str(exc))

        retryable = method_name in RETRYABLE_METHODS
        for attempt in range(self._max_retries + 1):
            try:
                with self._client_factory(api_key=api_key, headers={"User-Agent": USER_AGENT}) as client:
                    method = getattr(client, method_name)
                    result = method(normalized_symbol, **kwargs)
                break
            except HpsiMcpPaymentError as exc:
                return error_payload("payment_required", str(exc), status_code=exc.status_code, symbol=normalized_symbol)
            except HpsiMcpAuthError as exc:
                return error_payload("http_error", str(exc), status_code=exc.status_code, symbol=normalized_symbol)
            except HpsiMcpRateLimitError as exc:
                delay = retry_after_seconds(exc)
                if retryable and delay is not None and attempt < self._max_retries:
                    self._sleep(delay)
                    continue
                return error_payload("rate_limited", str(exc), status_code=exc.status_code, symbol=normalized_symbol)
            except HpsiMcpTimeoutError as exc:
                if retryable and attempt < self._max_retries:
                    self._sleep(min(0.5 * (2**attempt), 4.0))
                    continue
                return error_payload("request_timeout", str(exc), symbol=normalized_symbol)
            except HpsiMcpConnectionError as exc:
                return error_payload("request_failed", str(exc), symbol=normalized_symbol)
            except HpsiMcpResponseError as exc:
                return error_payload("invalid_json", str(exc), status_code=exc.status_code, symbol=normalized_symbol)
            except HpsiMcpAPIError as exc:
                if retryable and exc.status_code in RETRYABLE_STATUS_CODES and attempt < self._max_retries:
                    self._sleep(min(0.5 * (2**attempt), 4.0))
                    continue
                return error_payload("http_error", str(exc), status_code=exc.status_code, symbol=normalized_symbol)
            except Exception as exc:
                status_code = getattr(exc, "status_code", None)
                return error_payload("http_error", str(exc), status_code=status_code, symbol=normalized_symbol)
        else:
            raise AssertionError("retry loop exhausted without returning or breaking")

        try:
            if method_name == "get_ai_prediction":
                result = normalize_ai_prediction_result(result)
            if not isinstance(result, dict):
                return error_payload(
                    "invalid_response",
                    "The HPSILab service returned a non-object response.",
                    symbol=normalized_symbol,
                )
            return normalize_success_payload(result)
        except Exception as exc:
            status_code = getattr(exc, "status_code", None)
            return error_payload("http_error", str(exc), status_code=status_code, symbol=normalized_symbol)

    def call_batch(self, method_name: str, symbols: list[str], **kwargs: Any) -> list[dict[str, Any]]:
        """Call symbols in order and stop immediately on authentication failure."""
        results: list[dict[str, Any]] = []
        for symbol in symbols:
            result = self.call(method_name, symbol, **kwargs)
            results.append(result)
            if result.get("error") == "api_key_required" or result.get("status_code") in {401, 402, 403}:
                break
        return results

    def register_account(self, email: str) -> dict[str, Any]:
        """Register through an authenticated client; never bootstrap anonymously.

        Missing credentials return the same local `api_key_required` payload
        as every financial tool, before validating input or constructing the
        downstream client. New users register through the supplied HTTPS URL.
        """
        api_key = self._credential_provider.get_api_key()
        if not api_key:
            return api_key_required_payload()

        normalized_email = (email or "").strip()
        if "@" not in normalized_email or len(normalized_email) < 3:
            return error_payload(
                "invalid_email",
                "email must be a real address, for example 'you@example.com'. "
                "The verification link is sent there, and an address nobody "
                "reads leaves the account at the anonymous allowance.",
            )

        try:
            with self._client_factory(api_key=api_key, headers={"User-Agent": USER_AGENT}) as client:
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
