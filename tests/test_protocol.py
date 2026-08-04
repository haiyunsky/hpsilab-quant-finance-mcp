import asyncio
import json
import os
import sys
import unittest
import warnings
from pathlib import Path

from jsonschema.validators import validator_for
from starlette.exceptions import StarletteDeprecationWarning

warnings.filterwarnings(
    "ignore",
    message="Using `httpx` with `starlette.testclient` is deprecated.*",
    category=StarletteDeprecationWarning,
)

from starlette.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client
from mcp.types import LATEST_PROTOCOL_VERSION

from hpsilab_quant_finance_mcp import __version__
from hpsilab_quant_finance_mcp.server import create_http_app, mcp


class ToolSchemaTests(unittest.TestCase):
    def test_public_tool_names_and_flat_input_schemas(self):
        tools = asyncio.run(mcp.list_tools())
        expected_names = {
            "analyze_stock",
            "get_ai_prediction",
            "get_iv_radar",
            "get_option_pressure",
            "get_monte_carlo",
            "get_equity_curve",
            "get_pretrade_risk_scan",
            "generate_stock_images",
            "generate_stock_research_report",
            "register_account",
        }
        self.assertEqual({tool.name for tool in tools}, expected_names)

        for tool in tools:
            schema = tool.inputSchema
            self.assertEqual(schema["type"], "object", tool.name)
            self.assertNotIn("request", schema.get("properties", {}), tool.name)
            self.assertNotIn("input", schema.get("properties", {}), tool.name)
            self.assertTrue(tool.description, tool.name)
            self.assertIsNotNone(tool.outputSchema, tool.name)

            validator = validator_for(schema)
            validator.check_schema(schema)
            validator_for(tool.outputSchema).check_schema(tool.outputSchema)

            for parameter, parameter_schema in schema.get("properties", {}).items():
                branches = parameter_schema.get("anyOf", [parameter_schema])
                self.assertTrue(
                    parameter_schema.get("description") or any(branch.get("description") for branch in branches),
                    f"{tool.name}.{parameter}",
                )

    def test_protocol_error_adapter_preserves_structured_payload(self):
        result = asyncio.run(mcp.call_tool("analyze_stock", {"symbol": "NVDA"}))
        self.assertTrue(result.isError)
        self.assertEqual(result.structuredContent["error"], "api_key_required")
        self.assertEqual(json.loads(result.content[0].text), result.structuredContent)


class StdioProtocolTests(unittest.IsolatedAsyncioTestCase):
    async def test_initialize_lists_and_call_tool_over_stdio(self):
        environment = os.environ.copy()
        environment["HPSILAB_API_KEY"] = ""
        environment["PYTHONPATH"] = str(ROOT / "src")
        parameters = StdioServerParameters(
            command=sys.executable,
            args=["-m", "hpsilab_quant_finance_mcp.server"],
            env=environment,
        )

        async with stdio_client(parameters) as streams:
            async with ClientSession(*streams) as session:
                initialized = await session.initialize()
                self.assertEqual(initialized.serverInfo.version, __version__)
                self.assertIsNotNone(initialized.capabilities.tools)
                self.assertFalse(initialized.capabilities.resources.listChanged)
                self.assertFalse(initialized.capabilities.resources.subscribe)
                self.assertFalse(initialized.capabilities.prompts.listChanged)

                tools = await session.list_tools()
                self.assertEqual(len(tools.tools), 10)
                self.assertEqual((await session.list_resources()).resources, [])
                self.assertEqual((await session.list_prompts()).prompts, [])

                result = await session.call_tool("analyze_stock", {"symbol": "NVDA"})
                self.assertTrue(result.isError)
                self.assertEqual(result.structuredContent["error"], "api_key_required")


class StreamableHttpTests(unittest.TestCase):
    def test_initialize_over_streamable_http(self):
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": LATEST_PROTOCOL_VERSION,
                "capabilities": {},
                "clientInfo": {"name": "compatibility-test", "version": "1.0"},
            },
        }
        headers = {"Accept": "application/json, text/event-stream"}

        with TestClient(create_http_app(), base_url="http://127.0.0.1:8000") as client:
            response = client.post("/mcp", json=payload, headers=headers)
            self.assertEqual(response.status_code, 200, response.text)

            result = response.json()["result"]
            self.assertEqual(result["serverInfo"]["version"], __version__)
            self.assertIn("tools", result["capabilities"])
            self.assertFalse(result["capabilities"]["tools"]["listChanged"])
            self.assertFalse(result["capabilities"]["resources"]["listChanged"])
            self.assertFalse(result["capabilities"]["resources"]["subscribe"])
            self.assertFalse(result["capabilities"]["prompts"]["listChanged"])

            session_headers = {
                **headers,
                "Mcp-Session-Id": response.headers["Mcp-Session-Id"],
                "MCP-Protocol-Version": result["protocolVersion"],
            }
            initialized = client.post(
                "/mcp",
                json={"jsonrpc": "2.0", "method": "notifications/initialized"},
                headers=session_headers,
            )
            self.assertEqual(initialized.status_code, 202, initialized.text)

            listed = client.post(
                "/mcp",
                json={"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
                headers=session_headers,
            )
            self.assertEqual(listed.status_code, 200, listed.text)
            self.assertEqual(len(listed.json()["result"]["tools"]), 10)

            invalid_call = client.post(
                "/mcp",
                json={
                    "jsonrpc": "2.0",
                    "id": 3,
                    "method": "tools/call",
                    "params": {"name": "analyze_stock", "arguments": {}},
                },
                headers=session_headers,
            )
            self.assertEqual(invalid_call.status_code, 200, invalid_call.text)
            self.assertTrue(invalid_call.json()["result"]["isError"])


if __name__ == "__main__":
    unittest.main()
