import os
import sys
import unittest
from pathlib import Path
from unittest import mock

import httpx

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from hpsilab_mcp import (
    HpsiMcpAPIError,
    HpsiMcpAuthError,
    HpsiMcpConnectionError,
    HpsiMcpPaymentError,
    HpsiMcpRateLimitError,
    HpsiMcpTimeoutError,
)

from hpsilab_quant_finance_mcp.auth import EnvironmentApiKeyProvider
from hpsilab_quant_finance_mcp.service import (
    DISCLAIMER,
    USER_AGENT,
    QuantFinanceClient,
    QuantFinanceService,
    downstream_rate_limit_payload,
    error_payload,
    normalize_ai_prediction_result,
    normalize_success_payload,
    normalize_symbol,
    retry_after_seconds,
)


class FakeClient:
    def __init__(self, api_key, headers=None):
        self.api_key = api_key
        self.headers = headers or {}

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        return False

    def analyze_stock(self, symbol):
        return {"symbol": symbol, "signal": "Neutral"}


class NonObjectClient(FakeClient):
    def analyze_stock(self, symbol):
        return [symbol]


class PredictionClient(FakeClient):
    def get_ai_prediction(self, symbol):
        return '{"symbol": "' + symbol + '", "prediction": "Up"}'


class SingleItemListPredictionClient(FakeClient):
    def get_ai_prediction(self, symbol):
        return [{"symbol": symbol, "prediction": "Up"}]


class ServiceTests(unittest.TestCase):
    def test_environment_provider_strips_whitespace(self):
        with mock.patch.dict(os.environ, {"HPSILAB_API_KEY": "  hpsi_test  "}, clear=True):
            self.assertEqual(EnvironmentApiKeyProvider().get_api_key(), "hpsi_test")

    def test_normalize_symbol(self):
        self.assertEqual(normalize_symbol(" brk.b "), "BRK.B")
        with self.assertRaises(ValueError):
            normalize_symbol("NVIDIA INC")

    def test_success_payload_is_additive_and_does_not_overwrite(self):
        payload = normalize_success_payload({"symbol": "SPY", "status": "cached"})
        self.assertEqual(payload["status"], "cached")
        self.assertEqual(payload["disclaimer"], DISCLAIMER)

    def test_error_payload_has_stable_required_fields(self):
        payload = error_payload("invalid_symbol", "bad symbol", symbol="BAD SYMBOL")
        self.assertEqual(
            set(("status", "error_code", "message", "disclaimer", "symbol")) - payload.keys(),
            set(),
        )
        self.assertEqual(payload["status"], "error")

    def test_service_normalizes_success(self):
        with mock.patch.dict(os.environ, {"HPSILAB_API_KEY": "hpsi_test"}, clear=True):
            result = QuantFinanceService(client_factory=FakeClient).call("analyze_stock", "nvda")

        self.assertEqual(result["symbol"], "NVDA")
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["disclaimer"], DISCLAIMER)

    def test_missing_key_returns_exact_payload_without_constructing_client(self):
        client_factory = mock.Mock(side_effect=AssertionError("client must not be constructed"))

        with mock.patch.dict(os.environ, {}, clear=True):
            result = QuantFinanceService(client_factory=client_factory).call("analyze_stock", "NVDA")

        self.assertEqual(
            result,
            {
                "error": "api_key_required",
                "message": "A free API key is required.",
                "register_url": "https://hpsilab.com/register",
                "docs_url": "https://hpsilab.com/developer/v2",
            },
        )
        client_factory.assert_not_called()

    def test_client_uses_real_version_user_agent(self):
        client_factory = mock.Mock(side_effect=FakeClient)
        with mock.patch.dict(os.environ, {"HPSILAB_API_KEY": "hpsi_test"}, clear=True):
            QuantFinanceService(client_factory=client_factory).call("analyze_stock", "NVDA")

        self.assertNotEqual(USER_AGENT, "hpsilab-python-sdk/0.0.0")
        self.assertEqual(client_factory.call_args.kwargs["headers"]["User-Agent"], USER_AGENT)

    def test_downstream_429_preserves_registration_and_paid_guidance(self):
        body = {
            "error": "rate_limit_exceeded",
            "limit": 10,
            "window": "minute",
            "next_action": {
                "free": {"title": "Register Free", "credits": 100, "url": "https://hpsilab.com/register"},
                "pro": {"title": "Upgrade to Pro", "credits": 15_000, "url": "https://hpsilab.com/pricing"},
            },
        }
        error = HpsiMcpRateLimitError("slow down", status_code=429, body=body)

        result = downstream_rate_limit_payload(error, symbol="NVDA")

        self.assertEqual(result["error"], "rate_limit_exceeded")
        self.assertEqual(result["limit"], 10)
        self.assertEqual(result["next_action"], body["next_action"])

    def test_service_reuses_client_so_402_breaker_blocks_five_tool_sequence_locally(self):
        requests = 0

        def handler(request):
            nonlocal requests
            requests += 1
            return httpx.Response(402, json={"error": "Free API key required"})

        transport = httpx.MockTransport(handler)
        factory = mock.Mock(side_effect=lambda **kwargs: QuantFinanceClient(transport=transport, **kwargs))
        service = QuantFinanceService(client_factory=factory)
        with mock.patch.dict(os.environ, {"HPSILAB_API_KEY": "hpsi_bad"}, clear=True):
            results = [
                service.call(method_name, "PINS")
                for method_name in (
                    "get_ai_prediction",
                    "get_iv_radar",
                    "get_option_pressure",
                    "get_monte_carlo",
                    "analyze_stock",
                )
            ]

        self.assertEqual(results[0]["error_code"], "payment_required")
        self.assertTrue(all(result["error_code"] == "configuration_error" for result in results[1:]))
        self.assertTrue(all(result["status_code"] == 402 for result in results[1:]))
        self.assertEqual(requests, 1)
        factory.assert_called_once()
        service.close()

    def test_api_key_change_replaces_client_and_resets_breaker(self):
        requests = []

        def handler(request):
            requests.append(request.headers.get("Authorization"))
            if request.headers.get("Authorization") == "Bearer hpsi_bad":
                return httpx.Response(402, json={"error": "Free API key required"})
            return httpx.Response(200, json={"symbol": "PINS"})

        transport = httpx.MockTransport(handler)
        factory = mock.Mock(side_effect=lambda **kwargs: QuantFinanceClient(transport=transport, **kwargs))
        service = QuantFinanceService(client_factory=factory)
        with mock.patch.dict(os.environ, {"HPSILAB_API_KEY": "hpsi_bad"}, clear=True):
            self.assertEqual(service.call("get_ai_prediction", "PINS")["error_code"], "payment_required")
        with mock.patch.dict(os.environ, {"HPSILAB_API_KEY": "hpsi_good"}, clear=True):
            self.assertEqual(service.call("get_ai_prediction", "PINS")["status"], "success")

        self.assertEqual(len(requests), 2)
        self.assertEqual(factory.call_count, 2)
        service.close()


class ScriptedClient(FakeClient):
    outcomes = []
    calls = []
    seen_headers = []

    def __init__(self, api_key, headers=None):
        super().__init__(api_key, headers)
        type(self).seen_headers.append(self.headers)

    def _invoke(self, method_name, symbol, **kwargs):
        type(self).calls.append((method_name, symbol, kwargs))
        outcome = type(self).outcomes.pop(0)
        if isinstance(outcome, BaseException):
            raise outcome
        return outcome

    def analyze_stock(self, symbol, **kwargs):
        return self._invoke("analyze_stock", symbol, **kwargs)

    def __getattr__(self, method_name):
        return lambda symbol, **kwargs: self._invoke(method_name, symbol, **kwargs)


class RetryTests(unittest.TestCase):
    def setUp(self):
        ScriptedClient.outcomes = []
        ScriptedClient.calls = []
        ScriptedClient.seen_headers = []

    def call(self, outcomes, method_name="analyze_stock", max_retries=2):
        ScriptedClient.outcomes = list(outcomes)
        sleep = mock.Mock()
        with mock.patch.dict(os.environ, {"HPSILAB_API_KEY": "hpsi_test"}, clear=True):
            result = QuantFinanceService(
                client_factory=ScriptedClient,
                max_retries=max_retries,
                sleep_fn=sleep,
            ).call(method_name, "NVDA")
        return result, sleep

    def test_401_and_402_are_not_retried(self):
        errors = (
            HpsiMcpAuthError("invalid key", status_code=401),
            HpsiMcpPaymentError("payment required", status_code=402),
        )
        for error in errors:
            with self.subTest(status=error.status_code):
                ScriptedClient.calls = []
                result, sleep = self.call([error])
                self.assertEqual(result["status_code"], error.status_code)
                self.assertEqual(len(ScriptedClient.calls), 1)
                sleep.assert_not_called()

    def test_batch_stops_at_first_authentication_error(self):
        for status_code in (401, 403):
            with self.subTest(status_code=status_code):
                ScriptedClient.calls = []
                ScriptedClient.outcomes = [HpsiMcpAuthError("invalid key", status_code=status_code)]
                with mock.patch.dict(os.environ, {"HPSILAB_API_KEY": "hpsi_test"}, clear=True):
                    results = QuantFinanceService(client_factory=ScriptedClient).call_batch(
                        "analyze_stock", ["NVDA", "AAPL", "SPY"]
                    )

                self.assertEqual(len(results), 1)
                self.assertEqual(len(ScriptedClient.calls), 1)

    def test_429_honors_retry_after(self):
        error = HpsiMcpRateLimitError("slow down", status_code=429)
        error.response_headers = {"Retry-After": "3"}
        result, sleep = self.call([error, {"symbol": "NVDA"}])

        self.assertEqual(result["status"], "success")
        sleep.assert_called_once_with(3.0)
        self.assertEqual(len(ScriptedClient.calls), 2)

    def test_client_preserves_retry_after_response_header(self):
        transport = httpx.MockTransport(
            lambda request: httpx.Response(
                429,
                headers={"Retry-After": "4"},
                json={"message": "slow down"},
            )
        )
        with QuantFinanceClient(api_key="hpsi_test", transport=transport) as client:
            with self.assertRaises(HpsiMcpRateLimitError) as caught:
                client.get_monte_carlo("NVDA")

        self.assertEqual(caught.exception.response_headers["retry-after"], "4")
        self.assertEqual(retry_after_seconds(caught.exception), 4.0)

    def test_429_without_retry_after_is_not_retried(self):
        error = HpsiMcpRateLimitError("quota exhausted", status_code=429)
        result, sleep = self.call([error])

        self.assertEqual(result["error_code"], "rate_limited")
        self.assertEqual(len(ScriptedClient.calls), 1)
        sleep.assert_not_called()

    def test_timeout_and_recoverable_5xx_have_finite_retries(self):
        cases = (
            HpsiMcpTimeoutError("timeout"),
            HpsiMcpAPIError("unavailable", status_code=503),
        )
        for error in cases:
            with self.subTest(error=type(error).__name__):
                ScriptedClient.calls = []
                result, sleep = self.call([error, error, {"symbol": "NVDA"}])
                self.assertEqual(result["status"], "success")
                self.assertEqual(len(ScriptedClient.calls), 3)
                self.assertEqual(sleep.call_count, 2)

    def test_connection_and_other_http_errors_are_not_retried(self):
        errors = (
            HpsiMcpConnectionError("connection failed"),
            HpsiMcpAPIError("bad request", status_code=400),
        )
        for error in errors:
            with self.subTest(error=type(error).__name__):
                ScriptedClient.calls = []
                result, sleep = self.call([error])
                self.assertEqual(result["status"], "error")
                self.assertEqual(len(ScriptedClient.calls), 1)
                sleep.assert_not_called()

    def test_non_idempotent_artifact_timeout_is_not_retried(self):
        result, sleep = self.call(
            [HpsiMcpTimeoutError("timeout")],
            method_name="generate_stock_images",
        )

        self.assertEqual(result["error_code"], "request_timeout")
        self.assertEqual(len(ScriptedClient.calls), 1)
        sleep.assert_not_called()

    def test_non_object_sdk_response_becomes_structured_error(self):
        with mock.patch.dict(os.environ, {"HPSILAB_API_KEY": "hpsi_test"}, clear=True):
            result = QuantFinanceService(client_factory=NonObjectClient).call("analyze_stock", "SPY")

        self.assertEqual(result["status"], "error")
        self.assertEqual(result["error_code"], "invalid_response")

    def test_ai_prediction_accepts_sdk_json_object_response(self):
        with mock.patch.dict(os.environ, {"HPSILAB_API_KEY": "hpsi_test"}, clear=True):
            result = QuantFinanceService(client_factory=PredictionClient).call("get_ai_prediction", "nvda")

        self.assertEqual(result["symbol"], "NVDA")
        self.assertEqual(result["prediction"], "Up")
        self.assertEqual(result["status"], "success")

    def test_ai_prediction_accepts_single_object_list_response(self):
        with mock.patch.dict(os.environ, {"HPSILAB_API_KEY": "hpsi_test"}, clear=True):
            result = QuantFinanceService(client_factory=SingleItemListPredictionClient).call(
                "get_ai_prediction", "nvda"
            )

        self.assertEqual(result["symbol"], "NVDA")
        self.assertEqual(result["prediction"], "Up")
        self.assertEqual(result["status"], "success")

    def test_ai_prediction_rejects_non_object_json_response(self):
        self.assertIsNone(normalize_ai_prediction_result('["NVDA"]'))

    def test_ai_prediction_rejects_multiple_object_list_response(self):
        self.assertIsNone(normalize_ai_prediction_result([{"symbol": "NVDA"}, {"symbol": "AAPL"}]))


if __name__ == "__main__":
    unittest.main()
