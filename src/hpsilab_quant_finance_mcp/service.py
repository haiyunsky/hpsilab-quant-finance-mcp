"""Reusable service adapter shared by every MCP transport."""

from __future__ import annotations

import hashlib
import json
import math
import re
import time
from collections.abc import Callable
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from threading import RLock
from typing import Any, Protocol

import httpx
from hpsilab_mcp import (
    HpsiMcpAPIError,
    HpsiMcpAuthError,
    HpsiMcpClient,
    HpsiMcpConfigError,
    HpsiMcpConnectionError,
    HpsiMcpInsufficientCreditsError,
    HpsiMcpPaymentError,
    HpsiMcpRateLimitError,
    HpsiMcpResponseError,
    HpsiMcpSettlementUnknownError,
    HpsiMcpTimeoutError,
)
from hpsilab_mcp import register as hpsilab_register

from . import __version__
from .auth import CredentialProvider, EnvironmentApiKeyProvider
from .quota import BurstRateLimiter, RateLimited

DISCLAIMER = (
    "Research and educational output only. This is not investment advice, "
    "financial advice, or a recommendation to buy or sell any security."
)
SYMBOL_PATTERN = re.compile(r"^[A-Z][A-Z0-9.-]{0,15}$")
REGISTER_URL = "https://hpsilab.com/register"
PRICING_URL = "https://hpsilab.com/pricing"
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
    """Preserve Retry-After metadata exposed by the downstream response.

    The signature forwards whatever the SDK passes rather than restating it.
    It used to name `(self, response)` exactly, and when the SDK began passing
    `payment_refusal=` in 0.13.0 that override started raising `TypeError` on
    every non-2xx response — before the SDK could classify it. The typed
    exception this subclass exists to enrich was never constructed, and the
    service's bare `except Exception` turned every 401, 402, and 429 into an
    untyped `http_error` with no status code, which is also how the bounded
    retry on 429 stopped happening. An override that only decorates has no
    business restating a signature it does not read.
    """

    def _raise_for_status(self, response: httpx.Response, *args: Any, **kwargs: Any) -> None:
        try:
            super()._raise_for_status(response, *args, **kwargs)
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


def rate_limited_payload(violation: RateLimited, *, symbol: str | None = None) -> dict[str, Any]:
    """Map a local burst rejection to the shared structured error contract.

    Deliberately carries no registration or upgrade guidance. A 429 is a
    "you are going too fast" and nothing else; the one action that resolves
    it is waiting, and an upsell attached here sells a plan to someone whose
    problem costs two seconds to fix. The hosted API dropped the same fields
    from its own 429 on 2026-08-08 for the same reason.
    """
    payload = error_payload(
        "rate_limited",
        f"Local burst limit reached: {violation.limit} requests per {violation.window} "
        f"per API key. Retry in {math.ceil(violation.retry_after_seconds)}s.",
        status_code=429,
        symbol=symbol,
        details={
            "limit": violation.limit,
            "window": violation.window,
            "retry_after_seconds": violation.retry_after_seconds,
            "reset_at": violation.reset_at,
            **({"tool": violation.tool} if violation.tool else {}),
        },
    )
    payload.update(
        {
            "error": "rate_limit_exceeded",
            **({"tool": violation.tool} if violation.tool else {}),
            "limit": violation.limit,
            "used": violation.limit,
            "remaining": 0,
            "window": violation.window,
            "retry_after_seconds": violation.retry_after_seconds,
            "reset_at": violation.reset_at,
            "next_actions": [{"type": "retry_after", "seconds": math.ceil(violation.retry_after_seconds)}],
        }
    )
    return payload


def downstream_rate_limit_payload(exc: HpsiMcpRateLimitError, *, symbol: str | None = None) -> dict[str, Any]:
    """Preserve safe, actionable quota fields returned by the hosted API."""
    payload = error_payload("rate_limited", str(exc), status_code=exc.status_code, symbol=symbol)
    body = exc.body if isinstance(exc.body, dict) else {}
    for field in (
        "error",
        "tool",
        "limit",
        "used",
        "remaining",
        "window",
        "retry_after_seconds",
        "reset_at",
        # `next_actions` is the canonical machine-readable list; the four that
        # follow it are the older single-remedy fields. Passed through rather
        # than rebuilt: what the API sent about the caller in front of it is
        # more accurate than anything this process can infer, and dropping a
        # field it chose to send is not this layer's decision.
        "next_actions",
        "upgrade",
        "next_action",
        "register",
        "upgrade_hint",
    ):
        if field in body:
            payload[field] = body[field]
    return payload


def _credits_next_actions(
    body: dict[str, Any], *, register_url: str | None, upgrade_url: str | None
) -> list[dict[str, Any]]:
    """Return what this caller can actually do about an empty balance.

    The API's own list wins when it sent one: it knows things this process
    cannot, such as whether 100 Credits are already granted and waiting behind
    an unclicked verification link. Only the fallback is derived locally, and
    it offers exactly one remedy — registering, for a caller who has no
    account, or buying Credits for one who does. No `x402_payment` action
    appears here: a Credits refusal carries no offer, and naming a payment
    with nothing to settle is a dead end dressed as a choice.
    """
    actions = body.get("next_actions")
    if isinstance(actions, list) and actions and all(isinstance(action, dict) for action in actions):
        return actions
    if register_url:
        return [{"type": "register", "label": "Get 100 trial Credits", "url": register_url}]
    return [{"type": "upgrade", "label": "Get more Credits", "url": upgrade_url or PRICING_URL}]


def insufficient_credits_payload(exc: HpsiMcpInsufficientCreditsError, *, symbol: str | None = None) -> dict[str, Any]:
    """Map an empty Credit balance to its own error code, never to a rate limit.

    This is not `rate_limited` and not `http_error`. Waiting resolves the
    first and says nothing about this one; the second discards the two numbers
    an agent needs to decide anything (`credits_required` / `credits_remaining`)
    and leaves it with prose to pattern-match.
    """
    body = exc.body if isinstance(exc.body, dict) else {}
    payload = error_payload(
        "insufficient_credits",
        str(exc),
        status_code=exc.status_code or 402,
        symbol=symbol,
    )
    payload["error"] = "insufficient_credits"
    for field, value in (
        ("credits_required", exc.credits_required),
        ("credits_remaining", exc.credits_remaining),
        ("upgrade_url", exc.upgrade_url),
        # Only an anonymous caller gets this: registering is the one remedy
        # someone who already signed up cannot take, and rendering it for them
        # is a dead link that implies the fault is with their account.
        ("register", exc.register_url),
    ):
        if value is not None:
            payload[field] = value
    for field in ("tool", "upgrade", "upgrade_hint"):
        if field in body:
            payload[field] = body[field]
    # Always stated, always 0 on a refusal. "Nothing was charged" should be a
    # fact the caller reads rather than one it infers from a missing key.
    payload["credits_charged"] = 0
    payload["next_actions"] = _credits_next_actions(body, register_url=exc.register_url, upgrade_url=exc.upgrade_url)
    return payload


def settlement_unknown_payload(exc: HpsiMcpSettlementUnknownError, *, symbol: str | None = None) -> dict[str, Any]:
    """Report a payment whose outcome nobody can confirm, and offer nothing.

    The authorization left the process and the facilitator may have moved the
    money before failing to answer. Retrying signs a *new* authorization for
    the same logical call — a second payment for one piece of work — so this
    payload carries an empty `next_actions`: safety outranks conversion here,
    and an offer in this space is an invitation to pay twice. `call_id` is
    what a reconciliation run needs; it is the one thing worth keeping.
    """
    payload = error_payload(
        "settlement_unknown",
        str(exc),
        status_code=getattr(exc, "status_code", None),
        symbol=symbol,
    )
    payload.update(
        {
            "error": "settlement_unknown",
            "x402_status": "settlement_unknown",
            "settlement_status": exc.settlement_status or "unknown",
            "next_actions": [],
        }
    )
    if exc.call_id:
        payload["call_id"] = exc.call_id
    if exc.tool:
        payload["tool"] = exc.tool
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
        quota_limiter: BurstRateLimiter | None = None,
    ) -> None:
        if not isinstance(max_retries, int) or isinstance(max_retries, bool) or max_retries < 0:
            raise ValueError("max_retries must be a non-negative integer.")
        self._credential_provider = credential_provider or EnvironmentApiKeyProvider()
        self._client_factory = client_factory
        self._register_fn = register_fn
        self._max_retries = max_retries
        self._sleep = sleep_fn
        self._quota_limiter = quota_limiter or BurstRateLimiter()
        self._client_lock = RLock()
        self._client_config_id: str | None = None
        self._client: HpsiMcpClient | None = None
        self._auth_failure: tuple[str, int | None, str] | None = None

    @staticmethod
    def _config_id(api_key: str) -> str:
        """Identify an auth configuration without retaining another plaintext key."""
        return hashlib.sha256(api_key.encode("utf-8")).hexdigest()

    def _local_auth_failure(self, api_key: str, *, symbol: str | None = None) -> dict[str, Any] | None:
        config_id = self._config_id(api_key)
        with self._client_lock:
            failure = self._auth_failure
        if failure is None or failure[0] != config_id:
            return None
        _, status_code, message = failure
        return error_payload("configuration_error", message, status_code=status_code, symbol=symbol)

    def _trip_auth_circuit(self, api_key: str, status_code: int | None, message: str) -> None:
        with self._client_lock:
            self._auth_failure = (self._config_id(api_key), status_code, message)

    def _client_for(self, api_key: str) -> HpsiMcpClient:
        """Reuse one SDK client until authentication configuration changes.

        The SDK's authentication circuit breaker is intentionally
        instance-scoped. Reconstructing a client for every tool call would
        discard that state and allow every tool to send another known-invalid
        HTTP request. It latches on 401 only: a 402 is a price or an empty
        balance, and neither is fixed by building a new client.
        """
        config_id = self._config_id(api_key)
        with self._client_lock:
            if self._client is not None and self._client_config_id == config_id:
                return self._client

            previous = self._client
            self._client = self._client_factory(api_key=api_key, headers={"User-Agent": USER_AGENT})
            self._client_config_id = config_id
            if self._auth_failure is not None and self._auth_failure[0] != config_id:
                self._auth_failure = None
            if previous is not None:
                close = getattr(previous, "close", None)
                if callable(close):
                    close()
            return self._client

    def close(self) -> None:
        """Release the cached SDK client, if any."""
        with self._client_lock:
            client, self._client = self._client, None
            self._client_config_id = None
            self._auth_failure = None
            if client is not None:
                close = getattr(client, "close", None)
                if callable(close):
                    close()

    def call(self, method_name: str, symbol: str, **kwargs: Any) -> dict[str, Any]:
        api_key = self._credential_provider.get_api_key()
        if not api_key:
            return api_key_required_payload()

        try:
            normalized_symbol = normalize_symbol(symbol)
        except ValueError as exc:
            return error_payload("invalid_symbol", str(exc))

        local_failure = self._local_auth_failure(api_key, symbol=normalized_symbol)
        if local_failure is not None:
            return local_failure

        retryable = method_name in RETRYABLE_METHODS
        for attempt in range(self._max_retries + 1):
            violation = self._quota_limiter.check_and_consume(api_key, method_name)
            if violation is not None:
                return rate_limited_payload(violation, symbol=normalized_symbol)
            try:
                client = self._client_for(api_key)
                method = getattr(client, method_name)
                result = method(normalized_symbol, **kwargs)
                break
            # First, and outside the retry loop's reach on purpose. This one is
            # not an `HpsiMcpAPIError` in the SDK either, for the same reason:
            # the ordinary "an API error happened, try again" handler is the
            # line that pays twice here.
            except HpsiMcpSettlementUnknownError as exc:
                return settlement_unknown_payload(exc, symbol=normalized_symbol)
            # Before the auth circuit below, and that ordering is the point. An
            # empty balance is not a broken credential: the key is valid, and
            # the call made right after Credits are added has to reach the
            # network instead of being short-circuited by a latch set here.
            except HpsiMcpInsufficientCreditsError as exc:
                return insufficient_credits_payload(exc, symbol=normalized_symbol)
            except HpsiMcpConfigError as exc:
                message = str(exc)
                status_code = 402 if "402" in message else 401 if "401" in message else None
                self._trip_auth_circuit(api_key, status_code, message)
                return error_payload("configuration_error", message, status_code=status_code, symbol=normalized_symbol)
            # No circuit here. A payment challenge is a price, not a bad key —
            # the SDK stopped treating it as an authentication failure in
            # 0.13.0, and latching the whole process shut on one would take a
            # caller who touched a priced tool and lock it out of the free
            # ones it can still call.
            except HpsiMcpPaymentError as exc:
                return error_payload(
                    "payment_required", str(exc), status_code=exc.status_code, symbol=normalized_symbol
                )
            except HpsiMcpAuthError as exc:
                if exc.status_code in {401, 402}:
                    self._trip_auth_circuit(api_key, exc.status_code, str(exc))
                return error_payload("http_error", str(exc), status_code=exc.status_code, symbol=normalized_symbol)
            except HpsiMcpRateLimitError as exc:
                delay = retry_after_seconds(exc)
                if retryable and delay is not None and attempt < self._max_retries:
                    self._sleep(delay)
                    continue
                return downstream_rate_limit_payload(exc, symbol=normalized_symbol)
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
        """Call symbols in order and stop on anything the next symbol repeats.

        An empty balance and an unresolved settlement are checked by error code
        as well as status: the first is a 402 that the remaining symbols would
        each pay a request to rediscover, and the second may arrive with no
        status at all — it is raised from the payment path rather than from a
        response, and continuing the batch after it risks paying again.
        """
        results: list[dict[str, Any]] = []
        for symbol in symbols:
            result = self.call(method_name, symbol, **kwargs)
            results.append(result)
            if (
                result.get("error") == "api_key_required"
                or result.get("status_code") in {401, 402, 403}
                or result.get("error_code") in {"insufficient_credits", "settlement_unknown"}
            ):
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

        local_failure = self._local_auth_failure(api_key)
        if local_failure is not None:
            return local_failure

        normalized_email = (email or "").strip()
        if "@" not in normalized_email or len(normalized_email) < 3:
            return error_payload(
                "invalid_email",
                "email must be a real address, for example 'you@example.com'. "
                "The verification link is sent there, and an address nobody "
                "reads leaves the account at the anonymous allowance.",
            )

        try:
            violation = self._quota_limiter.check_and_consume(api_key, "register_account")
            if violation is not None:
                return rate_limited_payload(violation)
            client = self._client_for(api_key)
            result = client.register_account(normalized_email)
            if not isinstance(result, dict):
                return error_payload(
                    "invalid_response",
                    "The HPSILab service returned a non-object response.",
                )
            return normalize_success_payload(result)
        except HpsiMcpInsufficientCreditsError as exc:
            return insufficient_credits_payload(exc)
        except HpsiMcpConfigError as exc:
            message = str(exc)
            status_code = 402 if "402" in message else 401 if "401" in message else None
            self._trip_auth_circuit(api_key, status_code, message)
            return error_payload("configuration_error", message, status_code=status_code)
        except HpsiMcpPaymentError as exc:
            return error_payload("payment_required", str(exc), status_code=exc.status_code)
        except HpsiMcpAuthError as exc:
            if exc.status_code in {401, 402}:
                self._trip_auth_circuit(api_key, exc.status_code, str(exc))
            return error_payload("http_error", str(exc), status_code=exc.status_code)
        except HpsiMcpRateLimitError as exc:
            return downstream_rate_limit_payload(exc)
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
