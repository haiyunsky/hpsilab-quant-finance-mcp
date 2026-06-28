import os
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from hpsilab_mcp_server import server


class FakeResponse:
    def __init__(self, payload, status_code=200, reason="OK"):
        self._payload = payload
        self.status_code = status_code
        self.reason = reason
        self.text = str(payload)

    def json(self):
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise server.requests.exceptions.HTTPError(response=self)


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

    def test_get_uses_normalized_symbol_and_authorization_header(self):
        response_payload = {"symbol": "NVDA", "signal": "Neutral"}

        with mock.patch.dict(os.environ, {"HPSILAB_API_KEY": "test_api_key"}, clear=True):
            with mock.patch.object(
                server.requests,
                "get",
                return_value=FakeResponse(response_payload),
            ) as request_get:
                result = server.analyze_stock("nvda")

        self.assertEqual(result, response_payload)
        request_get.assert_called_once()
        args, kwargs = request_get.call_args
        self.assertEqual(args[0], "https://hpsilab.com/api/analyze_stock/NVDA")
        self.assertEqual(kwargs["headers"]["Authorization"], "Bearer test_api_key")
        self.assertEqual(kwargs["timeout"], server.TIMEOUT)

    def test_http_error_returns_structured_payload(self):
        with mock.patch.dict(os.environ, {"HPSILAB_API_KEY": "test_api_key"}, clear=True):
            with mock.patch.object(
                server.requests,
                "get",
                return_value=FakeResponse({"message": "free tier limit"}, status_code=403),
            ):
                result = server.get_iv_radar("SPY")

        self.assertEqual(result["status"], "error")
        self.assertEqual(result["error_code"], "http_error")
        self.assertEqual(result["status_code"], 403)
        self.assertEqual(result["message"], "free tier limit")
        self.assertEqual(result["symbol"], "SPY")


if __name__ == "__main__":
    unittest.main()
