from __future__ import annotations

from pathlib import Path
import unittest
from unittest.mock import patch

from tools.p17 import current_workspace_source_qualification_v42 as qualification


ROOT = Path(__file__).resolve().parents[3]


class CurrentWorkspaceSourceQualificationV42Tests(unittest.TestCase):
    def test_exact_current_source_and_runtime_qualification_pass(self) -> None:
        result = qualification.verify(ROOT)
        self.assertEqual(
            result["qualification_id"],
            "p17.current-workspace-source.v42.20260911",
        )
        self.assertEqual(result["source_successor_count"], 28)
        self.assertEqual(len(result["implementation_sources"]), 29)
        self.assertEqual(len(result["runtime_qualification_sources"]), 6)
        self.assertEqual(len(result["guard_sources"]), 3)

    def test_bounded_pull_claims_are_promoted_without_phase_promotion(self) -> None:
        claims = qualification.verify(ROOT)["claims"]
        self.assertTrue(claims["p17_durable_pull_verified"])
        self.assertTrue(
            claims["p17_durable_git_mirror_pull_current_pc_runtime_qualified"]
        )
        self.assertTrue(claims["p17_git_mirror_pull_conflict_preservation_verified"])
        self.assertFalse(claims["p17_git_mirror_remote_network_verified"])
        self.assertFalse(claims["p17_06_complete"])
        self.assertFalse(claims["actual_hangul"])
        self.assertFalse(claims["production"])
        self.assertFalse(claims["product_complete"])

    def test_runtime_qualification_claim_tamper_fails_closed(self) -> None:
        original = qualification.runtime.verify

        def tampered(root: Path) -> dict[str, object]:
            contract = dict(original(root))
            claims = dict(contract["claims"])
            claims["actual_remote_network"] = True
            contract["claims"] = claims
            return contract

        with patch.object(qualification.runtime, "verify", side_effect=tampered):
            with self.assertRaisesRegex(
                qualification.runtime.QualificationError, "runtime.claims"
            ):
                qualification.verify(ROOT)

    def test_implementation_history_tamper_fails_closed(self) -> None:
        original = qualification.runtime.git_blob

        def tampered(root: Path, revision: str, relative: str) -> bytes:
            raw = original(root, revision, relative)
            if relative == "crates/remote-sync-host/src/durable_git_pull.rs":
                return raw + b"\n"
            return raw

        with patch.object(qualification.runtime, "git_blob", side_effect=tampered):
            with self.assertRaisesRegex(
                qualification.runtime.QualificationError,
                "implementation.history",
            ):
                qualification.verify(ROOT)


if __name__ == "__main__":
    unittest.main()
