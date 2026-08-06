import re
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import hpsilab_quant_finance_mcp as package


class VersionTests(unittest.TestCase):
    def test_source_fallback_matches_declared_version(self):
        pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        declared = re.search(r'^version\s*=\s*"([^"]+)"', pyproject, re.MULTILINE)
        self.assertIsNotNone(declared)

        base, separator, local = package._FALLBACK_VERSION.partition("+")
        self.assertEqual(base, declared.group(1))
        self.assertEqual((separator, local), ("+", "source"))
        self.assertNotEqual(base, "0.0.0")

    def test_load_version_uses_real_source_fallback(self):
        with mock.patch.object(package, "version", side_effect=package.PackageNotFoundError):
            self.assertEqual(package._load_version(), package._FALLBACK_VERSION)

    def test_stale_installed_metadata_does_not_override_source_checkout(self):
        with mock.patch.object(package, "version", return_value="0.0.1"):
            self.assertEqual(package._load_version(), package._FALLBACK_VERSION)


if __name__ == "__main__":
    unittest.main()
