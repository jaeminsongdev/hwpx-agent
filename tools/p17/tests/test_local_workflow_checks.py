from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest


TOOLS_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS_DIR))
import run_local_workflow_checks as checks  # noqa: E402


class LocalWorkflowChecksTests(unittest.TestCase):
    def test_sources_are_unique_present_and_cover_every_runtime_layer(self) -> None:
        self.assertEqual(len(checks.SOURCES), len(set(checks.SOURCES)))
        for relative in checks.SOURCES:
            self.assertTrue((checks.ROOT / relative).is_file(), relative)
        for required in (
            "crates/local-workflow/src/lib.rs",
            "crates/local-companion-daemon/src/lib.rs",
            "web/local-companion-mcp/src/server.ts",
            "protocol/private/p17-local-mcp-v2.json",
        ):
            self.assertIn(required, checks.SOURCES)

    def test_receipt_keeps_real_clients_git_hangul_and_network_open(self) -> None:
        source = (checks.ROOT / "tools/p17/run_local_workflow_checks.py").read_text(
            encoding="utf-8"
        )
        self.assertIn('"actual_mcp_stdio": True', source)
        self.assertIn('"actual_codex_client": False', source)
        self.assertIn('"actual_personal_plugin": False', source)
        self.assertIn('"actual_git_commit": False', source)
        self.assertIn('"actual_hangul": False', source)
        self.assertIn('"network_used": False', source)
        self.assertNotIn("shell=True", source)

    def test_acceptance_covers_negative_and_preservation_boundaries(self) -> None:
        for required in (
            "input_bytes_preserved",
            "traversal_large_and_unknown_fields_rejected",
            "git_plan_bound_without_execution",
            "private_paths_content_and_token_absent",
        ):
            self.assertIn(required, checks.CHECKS)
        self.assertIn("call_rejected(", (checks.ROOT / checks.SOURCES[-4]).read_text(encoding="utf-8"))

    def test_v2_contract_is_additive_path_free_and_nonexecuting(self) -> None:
        contract = json.loads(
            (checks.ROOT / "protocol/private/p17-local-mcp-v2.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(contract["schema_version"], "hwpx-agent.local-mcp/v2")
        self.assertTrue(contract["migration"]["health_tool_preserved"])
        self.assertEqual([tool["name"] for tool in contract["tools"]], list(checks.TOOLS))
        self.assertFalse(contract["claims"]["accepts_paths"])
        self.assertFalse(contract["claims"]["executes_git"])
        publish = next(tool for tool in contract["tools"] if tool["method"] == "publish")
        self.assertTrue(publish["annotations"]["destructiveHint"])


if __name__ == "__main__":
    unittest.main()
