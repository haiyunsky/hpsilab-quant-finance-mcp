import os
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from hpsilab_mcp import HpsiMcpAuthError
from hpsilab_quant_finance_mcp import server


class FakeClient:
    """Stand-in for HpsiMcpClient: records the api_key it was built with and
    lets a test control what a named method returns or raises."""

    last_instance = None

    def __init__(self, api_key=None, **kwargs):
        self.api_key = api_key
        self.calls = []
        FakeClient.last_instance = self

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        return False

    def _record(self, name, symbol, **kwargs):
        self.calls.append((name, symbol, kwargs))


def make_fake_client(method_name, result=None, exception=None):
    class _Client(FakeClient):
        def __getattr__(self, name):
            if name != method_name:
                raise AttributeError(name)

            def _method(symbol, **kwargs):
                self._record(name, symbol, **kwargs)
                if exception is not None:
                    raise exception
                return result

            return _method

    return _Client


class ServerTests(unittest.TestCase):
    def test_normalize_symbol(self):
        self.assertEqual(server._normalize_symbol(" brk.b "), "BRK.B")
        self.assertEqual(server._normalize_symbol("spy"), "SPY")

    def test_invalid_symbol(self):
        result = server.analyze_stock("Nvidia Inc.")

        self.assertEqual(result["status"], "error")
        self.assertEqual(result["error_code"], "invalid_symbol")

    def test_missing_api_key_returns_clear_error(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            result = server.analyze_stock("NVDA")

        self.assertEqual(result["status"], "error")
        self.assertEqual(result["error_code"], "missing_api_key")
        self.assertEqual(result["symbol"], "NVDA")
        self.assertIn("HPSILAB_API_KEY", result["message"])

    def test_analyze_stock_uses_normalized_symbol_and_api_key(self):
        response_payload = {"symbol": "NVDA", "signal": "Neutral"}
        fake_cls = make_fake_client("analyze_stock", result=response_payload)

        with mock.patch.dict(os.environ, {"HPSILAB_API_KEY": "test_api_key"}, clear=True):
            with mock.patch.object(server, "HpsiMcpClient", fake_cls):
                result = server.analyze_stock("nvda")

        self.assertEqual(result, response_payload)
        self.assertEqual(FakeClient.last_instance.api_key, "test_api_key")
        self.assertEqual(FakeClient.last_instance.calls, [("analyze_stock", "NVDA", {})])

    def test_pretrade_risk_scan_uses_normalized_symbol(self):
        response_payload = {
            "symbol": "NVDA",
            "risk_level": "moderate",
            "checks": [{"name": "liquidity", "status": "pass"}],
        }
        fake_cls = make_fake_client("get_pretrade_risk_scan", result=response_payload)

        with mock.patch.dict(os.environ, {"HPSILAB_API_KEY": "test_api_key"}, clear=True):
            with mock.patch.object(server, "HpsiMcpClient", fake_cls):
                result = server.get_pretrade_risk_scan("nvda")

        self.assertEqual(result, response_payload)
        self.assertEqual(FakeClient.last_instance.calls, [("get_pretrade_risk_scan", "NVDA", {})])

    def test_http_error_returns_structured_payload(self):
        fake_cls = make_fake_client(
            "get_iv_radar",
            exception=HpsiMcpAuthError("quota exceeded", status_code=403),
        )

        with mock.patch.dict(os.environ, {"HPSILAB_API_KEY": "test_api_key"}, clear=True):
            with mock.patch.object(server, "HpsiMcpClient", fake_cls):
                result = server.get_iv_radar("SPY")

        self.assertEqual(result["status"], "error")
        self.assertEqual(result["error_code"], "http_error")
        self.assertEqual(result["status_code"], 403)
        self.assertEqual(result["message"], "quota exceeded")
        self.assertEqual(result["symbol"], "SPY")


if __name__ == "__main__":
    unittest.main()
