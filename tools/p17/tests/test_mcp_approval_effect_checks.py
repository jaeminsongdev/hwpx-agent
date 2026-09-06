"""Unit guards for the P17-08 MCP approval-effect acceptance runner."""
from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools/p17"))

import run_mcp_approval_effect_checks as checks  # noqa: E402


class McpApprovalEffectChecksTests(unittest.TestCase):
    def test_catalog_and_acceptance_checks_are_fixed_and_unique(self) -> None:
        self.assertEqual(len(checks.TOOLS), 7)
        self.assertEqual(len(set(checks.TOOLS)), 7)
        self.assertEqual(len(checks.CHECKS), 20)
        self.assertEqual(len(set(checks.CHECKS)), 20)
        self.assertEqual(checks.TOOLS[-2], checks.PREPARE_TOOL)
        self.assertEqual(checks.TOOLS[-1], checks.EXECUTE_TOOL)

    def test_bridge_has_only_an_app_visible_confirmation_surface(self) -> None:
        source = (ROOT / "web/local-companion-mcp/src/server.ts").read_text(
            encoding="utf-8"
        )
        package = json.loads(
            (ROOT / "web/local-companion-mcp/package.json").read_text(encoding="utf-8")
        )
        self.assertEqual(package["version"], "0.4.0")
        self.assertIn(checks.PREPARE_TOOL, source)
        self.assertIn(checks.EXECUTE_TOOL, source)
        self.assertIn('ui: { visibility: ["app"] }', source)
        self.assertIn("mintGitConfirmation", source)
        self.assertNotIn("local_companion_execute_git_commit\"", source)
        self.assertNotIn("mint_test_confirmation", source)

    def test_widget_calls_without_secret_identity_or_token_fields(self) -> None:
        source = (ROOT / "web/plugin-widget/src/git-approval-model.ts").read_text(
            encoding="utf-8"
        )
        start = source.index("export function confirmationArguments")
        confirmation = source[start:]
        self.assertNotIn("confirmation_token", confirmation)
        self.assertNotIn("actor_sha256", confirmation)
        self.assertNotIn("tenant_sha256", confirmation)


if __name__ == "__main__":
    unittest.main()
