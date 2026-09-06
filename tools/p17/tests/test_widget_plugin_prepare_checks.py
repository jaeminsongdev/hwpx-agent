from __future__ import annotations

from pathlib import Path
import sys
import unittest


TOOLS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS))
import run_widget_plugin_prepare_checks as checks  # noqa: E402


class WidgetPluginPrepareChecksTests(unittest.TestCase):
    def test_sources_are_unique_present_and_bind_v4_runtime(self) -> None:
        self.assertEqual(len(checks.SOURCES), len(set(checks.SOURCES)))
        for relative in checks.SOURCES:
            self.assertTrue((checks.ROOT / relative).is_file(), relative)
        self.assertIn("protocol/private/p17-local-mcp-v4.json", checks.SOURCES)
        self.assertIn("web/plugin-widget/src/git-approval-mcp-app-port.ts", checks.SOURCES)

    def test_acceptance_stays_prepare_only_and_fail_closed(self) -> None:
        source = (checks.ROOT / "tools/p17/run_widget_plugin_prepare_checks.py").read_text(
            encoding="utf-8"
        )
        self.assertEqual(checks.PLUGIN_VERSION, "0.4.0+codex.20260906130036")
        self.assertIn('"actual_trusted_ui": False', source)
        self.assertIn('"actual_git_effect": False', source)
        self.assertIn('"actual_hangul": False', source)
        self.assertIn('path_entries(APPROVAL_STATE) == ()', source)
        self.assertNotIn("shell=True", source)

    def test_plan_validator_rejects_promoted_or_secret_content(self) -> None:
        plan = {
            "approval": {
                "effect": "git_commit",
                "plan_sha256": "1" * 64,
                "target_sha256": "2" * 64,
            },
            "executed": False,
            "expected_head": checks.EXPECTED_HEAD,
            "expected_head_reference": "refs/heads/main",
            "expected_output_sha256": checks.EXPECTED_OUTPUT_SHA256,
            "message": checks.MESSAGE,
            "operation_id": checks.OPERATION_ID,
            "output_id": checks.OUTPUT_ID,
            "output_pathspec": f"output/{checks.OUTPUT_ID}.hwpx",
            "workspace_id": "primary",
        }
        self.assertEqual(checks.validate_prepare_plan(plan), plan)
        promoted = dict(plan)
        promoted["executed"] = True
        with self.assertRaisesRegex(checks.base.AcceptanceError, "prepare.plan"):
            checks.validate_prepare_plan(promoted)
        leaked = dict(plan)
        leaked["approval_challenge"] = "x" * 43
        with self.assertRaisesRegex(checks.base.AcceptanceError, "prepare.fields"):
            checks.validate_prepare_plan(leaked)


if __name__ == "__main__":
    unittest.main()
