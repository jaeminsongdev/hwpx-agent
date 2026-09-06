from __future__ import annotations

from pathlib import Path
import sys
import unittest


TOOLS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS))
import run_local_mcp_checks as checks  # noqa: E402


class LocalMcpChecksTests(unittest.TestCase):
    def test_sources_are_unique_present_and_cover_both_processes(self) -> None:
        self.assertEqual(len(checks.SOURCES), len(set(checks.SOURCES)))
        for relative in checks.SOURCES:
            self.assertTrue((checks.ROOT / relative).is_file(), relative)
        for required in (
            "crates/local-companion-daemon/src/main.rs",
            "web/local-companion-mcp/src/server.ts",
            "protocol/private/p17-local-mcp-v1.json",
        ):
            self.assertIn(required, checks.SOURCES)

    def test_receipt_claims_keep_plugin_hangul_and_network_open(self) -> None:
        source = (checks.ROOT / "tools/p17/run_local_mcp_checks.py").read_text(
            encoding="utf-8"
        )
        self.assertIn('"actual_codex_mcp": True', source)
        self.assertIn('"actual_personal_plugin": False', source)
        self.assertIn('"actual_hangul": False', source)
        self.assertIn('"network_used": False', source)
        self.assertNotIn("shell=True", source)

    def test_windows_build_tools_are_resolved_without_a_shell(self) -> None:
        source = (checks.ROOT / "tools/p17/run_local_mcp_checks.py").read_text(
            encoding="utf-8"
        )
        self.assertIn("shutil.which(arguments[0])", source)
        self.assertIn("[executable, *arguments[1:]]", source)
        self.assertNotIn("shell=True", source)

    def test_checked_in_contract_has_one_closed_health_tool(self) -> None:
        import json

        contract = json.loads(
            (checks.ROOT / "protocol/private/p17-local-mcp-v1.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(contract["schema_version"], "hwpx-agent.local-mcp/v1")
        self.assertEqual(contract["transport"], "stdio")
        self.assertEqual(len(contract["tools"]), 1)
        tool = contract["tools"][0]
        self.assertEqual(tool["name"], checks.TOOL_NAME)
        self.assertFalse(tool["inputSchema"]["additionalProperties"])
        self.assertFalse(contract["claims"]["opens_hangul"])
        self.assertFalse(contract["claims"]["accepts_paths"])


if __name__ == "__main__":
    unittest.main()
