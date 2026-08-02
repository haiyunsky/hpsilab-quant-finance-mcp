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

        self.assertEqual(len(tools), 10)
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

        # Tools that change state outside this process: the two artifact
        # generators, plus register_account (creates an account, sends an email,
        # and issues a fresh API key on every call).
        mutating = {
            "generate_stock_images",
            "generate_stock_research_report",
            "register_account",
        }
        for name, tool in tools.items():
            if name in mutating:
                continue
            annotations = tool.annotations
            self.assertTrue(annotations.readOnlyHint, name)
            self.assertFalse(annotations.destructiveHint, name)
            self.assertTrue(annotations.idempotentHint, name)
            self.assertTrue(annotations.openWorldHint, name)

    def test_register_account_is_annotated_as_mutating(self):
        """It must not be advertised as read-only: a client that trusts
        readOnlyHint could otherwise call it speculatively and create accounts."""
        tools = {tool.name: tool for tool in asyncio.run(server.mcp.list_tools())}
        annotations = tools["register_account"].annotations

        self.assertFalse(annotations.readOnlyHint)
        self.assertFalse(annotations.idempotentHint)
        self.assertFalse(annotations.destructiveHint)
        self.assertTrue(annotations.openWorldHint)

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
        # The error must name the way out. A caller with no key and no idea
        # how to get one is exactly who reads this message.
        self.assertIn("register_account", result["message"])

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


def make_fake_register_client(result=None, exception=None):
    """register_account takes an email, not a ticker, so it needs its own
    stand-in rather than make_fake_client's (symbol, **kwargs) shape."""

    class _Client(FakeClient):
        def register_account(self, email, **kwargs):
            self._record("register_account", email, **kwargs)
            if exception is not None:
                raise exception
            return result

    return _Client


def make_fake_register_fn(result=None, exception=None):
    """Stand-in for hpsilab_mcp.register — the no-key bootstrap path.

    Not client-shaped: it's a plain module-level function
    (`register(*, email) -> dict`), unlike `client.register_account`, which is
    an instance method on a constructed `HpsiMcpClient`. hpsilab-mcp >=0.11.0
    added it precisely because `HpsiMcpClient(api_key="")` now refuses to
    construct — there is no client to call an instance method on until a key
    exists, which is the whole problem this function solves.
    """
    calls = []

    def _fn(*, email):
        calls.append(email)
        if exception is not None:
            raise exception
        return result

    _fn.calls = calls
    return _fn


class RegisterAccountTests(unittest.TestCase):
    PAYLOAD = {
        "email": "agent@example.com",
        "tier": "free",
        "email_verified": False,
        "api_key": "hpsi_newkey",
        "already_registered": False,
        "message": "Registered.",
    }

    def test_works_without_an_api_key(self):
        """The whole point of the tool: every other tool refuses with
        missing_api_key, and this one must not — it is how a caller with no key
        obtains one. No key configured means no client can even be
        constructed (hpsilab-mcp >=0.11.0 requires api_key or wallet), so this
        must go through the standalone register_fn, not client_factory."""
        register_fn = make_fake_register_fn(result=self.PAYLOAD)
        fake_cls = make_fake_register_client(result={**self.PAYLOAD, "api_key": "should-not-be-used"})

        with mock.patch.dict(os.environ, {}, clear=True):
            service = QuantFinanceService(client_factory=fake_cls, register_fn=register_fn)
            with mock.patch.object(server, "_service", service):
                FakeClient.last_instance = None
                result = server.register_account("agent@example.com")

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["api_key"], "hpsi_newkey")
        self.assertEqual(register_fn.calls, ["agent@example.com"])
        # client_factory must not be touched at all on the no-key path — it
        # can't be, HpsiMcpClient(api_key="") raises in the real SDK now.
        self.assertIsNone(FakeClient.last_instance)

    def test_passes_an_existing_key_through_when_present(self):
        """A configured key uses the existing client instance method, not
        register_fn — the SDK leaves that credential in place rather than
        swapping it."""
        fake_cls = make_fake_register_client(result={**self.PAYLOAD, "already_registered": True})
        register_fn = make_fake_register_fn(result=self.PAYLOAD)

        with mock.patch.dict(os.environ, {"HPSILAB_API_KEY": "existing_key"}, clear=True):
            service = QuantFinanceService(client_factory=fake_cls, register_fn=register_fn)
            with mock.patch.object(server, "_service", service):
                result = server.register_account("agent@example.com")

        self.assertEqual(result["status"], "success")
        self.assertTrue(result["already_registered"])
        self.assertEqual(FakeClient.last_instance.api_key, "existing_key")
        self.assertEqual(register_fn.calls, [])

    def test_rejects_a_malformed_email_without_calling_the_api(self):
        register_fn = make_fake_register_fn(result=self.PAYLOAD)

        with mock.patch.object(server, "_service", QuantFinanceService(register_fn=register_fn)):
            result = server.register_account("not-an-email")

        self.assertEqual(result["status"], "error")
        self.assertEqual(result["error_code"], "invalid_email")
        self.assertEqual(register_fn.calls, [])

    def test_email_collision_is_surfaced_not_retried(self):
        """A 409 means the address belongs to someone else. It must reach the
        caller as an error — an agent must never be able to attach itself to a
        stranger's account."""
        register_fn = make_fake_register_fn(
            exception=HpsiMcpAuthError("That email is already registered.", status_code=409)
        )

        with mock.patch.dict(os.environ, {}, clear=True):
            with mock.patch.object(server, "_service", QuantFinanceService(register_fn=register_fn)):
                result = server.register_account("someone-else@example.com")

        self.assertEqual(result["status"], "error")
        self.assertEqual(result["status_code"], 409)

    def test_trims_surrounding_whitespace(self):
        register_fn = make_fake_register_fn(result=self.PAYLOAD)

        with mock.patch.dict(os.environ, {}, clear=True):
            with mock.patch.object(server, "_service", QuantFinanceService(register_fn=register_fn)):
                server.register_account("  agent@example.com  ")

        self.assertEqual(register_fn.calls, ["agent@example.com"])


if __name__ == "__main__":
    unittest.main()
