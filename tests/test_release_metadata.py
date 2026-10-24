"""Release metadata must agree with the tool surface the server registers.

AGENTS.md treats tool names, versions, pricing statements, and tool counts as
one contract across code, manifests, and documentation. These tests read the
published files so a release cannot ship them out of sync.
"""

import asyncio
import json
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from hpsilab_quant_finance_mcp import server  # noqa: E402

PRO_TOOLS = {"get_pretrade_risk_scan", "generate_stock_research_report"}
# The sdist ships tests but not the registry manifests, so these
# checks run from a repository checkout only.
REPO_FILES_PRESENT = all(path.is_file() for path in (ROOT / "server.json", ROOT / "manifest.json"))
requires_repo_files = unittest.skipUnless(REPO_FILES_PRESENT, "release files are not in the sdist")


def _declared_version() -> str:
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    return re.search(r'^version\s*=\s*"([^"]+)"', pyproject, re.MULTILINE).group(1)


def _tools():
    return {tool.name: tool for tool in asyncio.run(server.mcp.list_tools())}


@requires_repo_files
class ManifestConsistencyTests(unittest.TestCase):
    def test_versions_are_synchronized(self):
        version = _declared_version()
        server_json = json.loads((ROOT / "server.json").read_text(encoding="utf-8"))
        manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))

        self.assertEqual(server_json["version"], version)
        self.assertEqual({package["version"] for package in server_json["packages"]}, {version})
        self.assertEqual(manifest["version"], version)

    def test_manifest_lists_exactly_the_registered_tools(self):
        manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual({tool["name"] for tool in manifest["tools"]}, set(_tools()))
        self.assertEqual(len(_tools()), 10)


class CreditMetadataTests(unittest.TestCase):
    def test_every_research_tool_advertises_its_credit_price(self):
        tools = _tools()
        self.assertEqual(set(server.CREDIT_PRICES), set(tools) - {"register_account"})
        for name, credits in server.CREDIT_PRICES.items():
            self.assertIsInstance(credits, int, name)
            self.assertGreater(credits, 0, name)
            self.assertEqual(tools[name].meta["x-credits"], credits, name)
        self.assertNotIn("x-credits", tools["register_account"].meta)

    def test_pro_tools_say_signed_in_accounts_pay_credits(self):
        tools = _tools()
        for name in PRO_TOOLS:
            self.assertEqual(tools[name].meta["x-access"]["signed_in"], "credits", name)


if __name__ == "__main__":
    unittest.main()
