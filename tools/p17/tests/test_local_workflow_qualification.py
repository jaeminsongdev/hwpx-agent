from __future__ import annotations

from pathlib import Path
import sys
import unittest


TOOLS_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS_DIR))
import local_workflow_qualification as qualification  # noqa: E402


class LocalWorkflowQualificationTests(unittest.TestCase):
    def test_sources_are_unique_present_and_split_runtime_from_guards(self) -> None:
        combined = qualification.RUNTIME_SOURCES + qualification.GUARD_SOURCES
        self.assertEqual(len(combined), len(set(combined)))
        for relative in combined:
            self.assertTrue((qualification.ROOT / relative).is_file(), relative)
        self.assertIn("crates/local-workflow/src/lib.rs", qualification.RUNTIME_SOURCES)
        self.assertIn(
            "implementation/p17/P17-05_LOCAL_WORKFLOW_MCP_V2.md",
            qualification.GUARD_SOURCES,
        )

    def test_claims_do_not_promote_stdio_to_codex_git_or_hangul(self) -> None:
        self.assertTrue(qualification.CLAIMS["actual_mcp_stdio"])
        self.assertTrue(qualification.CLAIMS["path_free_public_inputs"])
        self.assertTrue(qualification.CLAIMS["source_preserved"])
        for open_claim in (
            "actual_codex_client",
            "actual_personal_plugin",
            "actual_git_commit",
            "actual_hangul",
            "network_used",
            "phase_complete",
        ):
            self.assertFalse(qualification.CLAIMS[open_claim], open_claim)

    def test_expected_receipt_is_exact_and_has_sixteen_checks(self) -> None:
        receipt = qualification.expected_receipt()
        qualification.validate_receipt(receipt)
        self.assertEqual(receipt["check_count"], 16)
        changed = dict(receipt)
        changed["actual_codex_client"] = True
        with self.assertRaises(qualification.QualificationError):
            qualification.validate_receipt(changed)

    def test_qualification_uses_exact_commit_blobs_without_shell(self) -> None:
        source = (
            qualification.ROOT / "tools/p17/local_workflow_qualification.py"
        ).read_text(encoding="utf-8")
        self.assertIn('f"{BASE_COMMIT}:{relative}"', source)
        self.assertIn("require_runtime_matches_base()", source)
        self.assertNotIn("shell=True", source)


if __name__ == "__main__":
    unittest.main()
