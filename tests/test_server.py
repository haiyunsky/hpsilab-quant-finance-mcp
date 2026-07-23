import asyncio
import io
import os
import sys
import unittest
from contextlib import redirect_stderr
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from hpsilab_mcp import HpsiMcpAuthError

from hpsilab_quant_finance_mcp import server
from hpsilab_quant_finance_mcp.service import QuantFinanceService


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
    def test_server_advertises_cross_tool_instructions(self):
        self.assertEqual(server.mcp._mcp_server.version, server.__version__)
        self.assertIn("never execute trades", server.mcp.instructions)
        self.assertIn("not idempotent", server.mcp.instructions)

    def test_transport_cli_defaults_to_stdio_and_protects_remote_binding(self):
        self.assertEqual(server._parse_args([]).transport, "stdio")
        http_args = server._parse_args(["--transport", "streamable-http"])
        self.assertEqual(http_args.host, "127.0.0.1")
        self.assertEqual(http_args.port, 8000)

        with redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                server._parse_args(["--transport", "streamable-http", "--host", "0.0.0.0"])

    def test_all_tools_expose_explicit_boolean_annotations(self):
        tools = asyncio.run(server.mcp.list_tools())
        required_hints = (
            "readOnlyHint",
            "destructiveHint",
            "idempotentHint",
            "openWorldHint",
        )

        self.assertEqual(len(tools), 9)
        for tool in tools:
            self.assertIsNotNone(tool.annotations, tool.name)
            for hint in required_hints:
                value = getattr(tool.annotations, hint)
                self.assertIs(type(value), bool, f"{tool.name}.{hint}={value!r}")

    def test_artifact_generators_are_non_destructive_creates(self):
        tools = {tool.name: tool for tool in asyncio.run(server.mcp.list_tools())}
        for name in ("generate_stock_images", "generate_stock_research_report"):
            annotations = tools[name].annotations
            self.assertFalse(annotations.readOnlyHint, name)
            self.assertFalse(annotations.destructiveHint, name)
            self.assertFalse(annotations.idempotentHint, name)
            self.assertTrue(annotations.openWorldHint, name)

    def test_analysis_tools_are_read_only_idempotent_and_open_world(self):
        tools = {tool.name: tool for tool in asyncio.run(server.mcp.list_tools())}

        for name, tool in tools.items():
            if name in {"generate_stock_images", "generate_stock_research_report"}:
                continue
            annotations = tool.annotations
            self.assertTrue(annotations.readOnlyHint, name)
            self.assertFalse(annotations.destructiveHint, name)
            self.assertTrue(annotations.idempotentHint, name)
            self.assertTrue(annotations.openWorldHint, name)

    def test_image_type_schema_has_explicit_enum(self):
        tools = {tool.name: tool for tool in asyncio.run(server.mcp.list_tools())}
        types_schema = tools["generate_stock_images"].inputSchema["properties"]["types"]
        item_schema = next(branch["items"] for branch in types_schema["anyOf"] if branch.get("type") == "array")
        self.assertEqual(
            item_schema["enum"],
            ["ai_prediction", "iv_radar", "option_pressure", "monte_carlo", "equity_curves"],
        )

    def test_generate_images_forwards_force_and_types(self):
        fake_cls = make_fake_client("generate_stock_images", result={"symbol": "NVDA", "images": []})
        selected = ["iv_radar", "option_pressure"]

        with mock.patch.dict(os.environ, {"HPSILAB_API_KEY": "test_api_key"}, clear=True):
            with mock.patch.object(server, "_service", QuantFinanceService(client_factory=fake_cls)):
                result = server.generate_stock_images("nvda", force=False, types=selected)

        self.assertEqual(result["symbol"], "NVDA")
        self.assertEqual(
            FakeClient.last_instance.calls,
            [("generate_stock_images", "NVDA", {"force": False, "types": selected})],
        )

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
            with mock.patch.object(server, "_service", QuantFinanceService(client_factory=fake_cls)):
                result = server.analyze_stock("nvda")

        self.assertEqual(result["symbol"], "NVDA")
        self.assertEqual(result["signal"], "Neutral")
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["disclaimer"], server.DISCLAIMER)
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
            with mock.patch.object(server, "_service", QuantFinanceService(client_factory=fake_cls)):
                result = server.get_pretrade_risk_scan("nvda")

        self.assertEqual(result["symbol"], "NVDA")
        self.assertEqual(result["risk_level"], "moderate")
        self.assertEqual(result["status"], "success")
        self.assertEqual(FakeClient.last_instance.calls, [("get_pretrade_risk_scan", "NVDA", {})])

    def test_http_error_returns_structured_payload(self):
        fake_cls = make_fake_client(
            "get_iv_radar",
            exception=HpsiMcpAuthError("quota exceeded", status_code=403),
        )

        with mock.patch.dict(os.environ, {"HPSILAB_API_KEY": "test_api_key"}, clear=True):
            with mock.patch.object(server, "_service", QuantFinanceService(client_factory=fake_cls)):
                result = server.get_iv_radar("SPY")

        self.assertEqual(result["status"], "error")
        self.assertEqual(result["error_code"], "http_error")
        self.assertEqual(result["status_code"], 403)
        self.assertEqual(result["message"], "quota exceeded")
        self.assertEqual(result["symbol"], "SPY")


if __name__ == "__main__":
    unittest.main()
