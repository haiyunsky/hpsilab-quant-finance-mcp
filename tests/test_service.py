import os
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from hpsilab_quant_finance_mcp.auth import EnvironmentApiKeyProvider
from hpsilab_quant_finance_mcp.service import (
    DISCLAIMER,
    QuantFinanceService,
    error_payload,
    normalize_success_payload,
    normalize_symbol,
)


class FakeClient:
    def __init__(self, api_key):
        self.api_key = api_key

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        return False

    def analyze_stock(self, symbol):
        return {"symbol": symbol, "signal": "Neutral"}


class NonObjectClient(FakeClient):
    def analyze_stock(self, symbol):
        return [symbol]


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

    def test_non_object_sdk_response_becomes_structured_error(self):
        with mock.patch.dict(os.environ, {"HPSILAB_API_KEY": "hpsi_test"}, clear=True):
            result = QuantFinanceService(client_factory=NonObjectClient).call("analyze_stock", "SPY")

        self.assertEqual(result["status"], "error")
        self.assertEqual(result["error_code"], "invalid_response")


if __name__ == "__main__":
    unittest.main()
