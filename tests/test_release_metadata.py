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

SKILL = ROOT / "skills" / "hpsilab-quant-research" / "SKILL.md"
PRO_TOOLS = {"get_pretrade_risk_scan", "generate_stock_research_report"}
# The sdist ships tests but not the registry manifests or the skill, so these
# checks run from a repository checkout only.
REPO_FILES_PRESENT = all(path.is_file() for path in (ROOT / "server.json", ROOT / "manifest.json", SKILL))
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
        self.assertIn(f"package version {version}", SKILL.read_text(encoding="utf-8"))

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


@requires_repo_files
class SkillConsistencyTests(unittest.TestCase):
    def setUp(self):
        self.text = SKILL.read_text(encoding="utf-8")

    def test_skill_tool_table_matches_names_and_credit_prices(self):
        rows = re.findall(r"^\| [^|]+ \| `(\w+)` \| [^|]+ \| (\d+|none) \|$", self.text, re.MULTILINE)
        table = dict(rows)
        self.assertEqual(set(table), set(_tools()))
        for name, credits in server.CREDIT_PRICES.items():
            self.assertEqual(table[name], str(credits), name)
        self.assertEqual(table["register_account"], "none")

    def test_skill_error_table_covers_every_error_code_the_package_returns(self):
        source = (ROOT / "src" / "hpsilab_quant_finance_mcp" / "service.py").read_text(encoding="utf-8")
        produced = set(re.findall(r'error_payload\(\s*"(\w+)"', source)) | {"api_key_required"}
        error_section = self.text.split("## Handling errors", 1)[1].split("\n## ", 1)[0]
        documented = set(re.findall(r"`(\w+)`", error_section))
        self.assertEqual(produced - documented, set())

    def test_skill_states_the_horizon_of_every_forecast(self):
        self.assertIn("**next trading day**", self.text)
        self.assertIn("**10 trading days**", self.text)
        self.assertIn("methodology.monteCarlo.horizonDays", self.text)


if __name__ == "__main__":
    unittest.main()
