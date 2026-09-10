from __future__ import annotations

from pathlib import Path
import unittest
from unittest.mock import patch

from tools.p17 import frozen_current_source_v43 as qualification


ROOT = Path(__file__).resolve().parents[3]


class CurrentWorkspaceSourceQualificationV43Tests(unittest.TestCase):
    def test_historical_qualification_uses_frozen_git_state(self) -> None:
        result = qualification.verify(ROOT)
        self.assertEqual(
            result["qualification_id"],
            "p17.current-workspace-source.v43.20260911",
        )
        self.assertFalse(result["mutable_worktree_sources_read"])

    def test_exact_source_counts_are_preserved(self) -> None:
        result = qualification.verify(ROOT)
        self.assertEqual(result["implementation_source_count"], 10)
        self.assertEqual(result["runtime_qualification_source_count"], 2)
        self.assertEqual(result["source_successor_count"], 28)
        self.assertEqual(result["guard_source_count"], 3)
        self.assertEqual(result["claim_count"], 66)

    def test_custody_claims_remain_frozen_without_phase_promotion(self) -> None:
        result = qualification.verify(ROOT)
        self.assertTrue(result["credential_store_mechanism_verified"])
        self.assertTrue(result["receipt_blob_verified"])
        self.assertTrue(result["synthetic_credential_only"])
        self.assertFalse(result["real_service_credential"])
        self.assertFalse(result["credential_issuance_or_rotation"])
        self.assertFalse(result["actual_remote_network"])
        self.assertFalse(result["production"])
        self.assertFalse(result["product_complete"])

    def test_implementation_history_tamper_fails_closed(self) -> None:
        original = qualification.git_blob

        def tampered(
            root: Path, revision: str, relative: str, maximum: int = 4_000_000
        ) -> bytes:
            raw = original(root, revision, relative, maximum)
            if relative == "crates/windows-credential-custody/src/lib.rs":
                return b"tampered"
            return raw

        with patch.object(qualification, "git_blob", side_effect=tampered):
            with self.assertRaisesRegex(
                qualification.FrozenSourceV43Error, "implementation.bytes"
            ):
                qualification.verify(ROOT)


if __name__ == "__main__":
    unittest.main()
