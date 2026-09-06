from __future__ import annotations

from pathlib import Path
import sys
import unittest


TOOLS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS))
import run_main_bound_plugin_checks as checks  # noqa: E402


class MainBoundPluginChecksTests(unittest.TestCase):
    def test_sources_are_unique_present_and_include_predecessor_harness(self) -> None:
        self.assertEqual(len(checks.SOURCES), len(set(checks.SOURCES)))
        for relative in checks.SOURCES:
            self.assertTrue((checks.ROOT / relative).is_file(), relative)
        self.assertIn("tools/p17/run_personal_plugin_checks.py", checks.SOURCES)

    def test_successor_requires_main_binding_and_cachebuster(self) -> None:
        source = (
            checks.ROOT / "tools/p17/run_main_bound_plugin_checks.py"
        ).read_text(encoding="utf-8")
        self.assertIn('Path("D:/개발/hwpx-agent").resolve()', source)
        self.assertRegex(checks.PLUGIN_VERSION, r"^0\.1\.0\+codex\.[0-9]{14}$")
        self.assertIn('"main_root_bound": True', source)
        self.assertIn('"actual_hangul": False', source)
        self.assertNotIn("shell=True", source)


if __name__ == "__main__":
    unittest.main()
