from __future__ import annotations

from pathlib import Path
import unittest
from unittest.mock import patch

from tools.p17 import frozen_current_source_v42 as qualification


ROOT = Path(__file__).resolve().parents[3]


class CurrentWorkspaceSourceQualificationV42Tests(unittest.TestCase):
    def test_historical_qualification_uses_frozen_git_state(self) -> None:
        result = qualification.verify(ROOT)
        self.assertEqual(
            result["qualification_id"],
            "p17.current-workspace-source.v42.20260911",
        )
        self.assertFalse(result["mutable_worktree_sources_read"])

    def test_exact_source_counts_are_preserved(self) -> None:
        result = qualification.verify(ROOT)
        self.assertEqual(result["implementation_source_count"], 29)
        self.assertEqual(result["runtime_qualification_source_count"], 6)
        self.assertEqual(result["source_successor_count"], 28)
        self.assertEqual(result["guard_source_count"], 3)
        self.assertEqual(result["claim_count"], 62)

    def test_bounded_pull_claims_remain_frozen_without_phase_promotion(self) -> None:
        result = qualification.verify(ROOT)
        self.assertTrue(result["durable_pull_runtime_verified"])
        self.assertTrue(result["receipt_blob_verified"])
        self.assertTrue(result["durable_pull"])
        self.assertFalse(result["actual_remote_network"])
        self.assertFalse(result["actual_hangul"])
        self.assertFalse(result["production"])
        self.assertFalse(result["product_complete"])

    def test_implementation_history_tamper_fails_closed(self) -> None:
        original = qualification.git_blob

        def tampered(
            root: Path, revision: str, relative: str, maximum: int = 4_000_000
        ) -> bytes:
            raw = original(root, revision, relative, maximum)
            if relative == "crates/remote-sync-host/src/durable_git_pull.rs":
                return b"tampered"
            return raw

        with patch.object(qualification, "git_blob", side_effect=tampered):
            with self.assertRaisesRegex(
                qualification.FrozenSourceV42Error, "implementation.bytes"
            ):
                qualification.verify(ROOT)


if __name__ == "__main__":
    unittest.main()
