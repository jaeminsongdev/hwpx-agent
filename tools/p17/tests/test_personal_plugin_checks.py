from __future__ import annotations

from pathlib import Path
import sys
import unittest


TOOLS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS))
import run_personal_plugin_checks as checks  # noqa: E402


class PersonalPluginChecksTests(unittest.TestCase):
    def test_sources_are_unique_present_and_bounded(self) -> None:
        self.assertEqual(len(checks.SOURCES), len(set(checks.SOURCES)))
        for relative in checks.SOURCES:
            self.assertTrue((checks.ROOT / relative).is_file(), relative)

    def test_claims_separate_product_network_from_codex_control_plane(self) -> None:
        source = (
            checks.ROOT / "tools/p17/run_personal_plugin_checks.py"
        ).read_text(encoding="utf-8")
        self.assertIn('"actual_codex_plugin": True', source)
        self.assertIn('"actual_hangul": False', source)
        self.assertIn('"product_network_enabled": False', source)
        self.assertIn('"codex_service_used": True', source)

    def test_fresh_session_forbids_shell_hangul_and_file_inspection(self) -> None:
        source = (
            checks.ROOT / "tools/p17/run_personal_plugin_checks.py"
        ).read_text(encoding="utf-8")
        self.assertIn('item.get("type") == "command_execution"', source)
        self.assertIn("Do not run shell commands, open Hangul, or inspect files.", source)
        self.assertIn('"--ephemeral"', source)
        self.assertIn('"read-only"', source)
        self.assertNotIn("shell=True", source)


if __name__ == "__main__":
    unittest.main()
