from __future__ import annotations

from pathlib import Path
import unittest

from tools.p17 import frozen_current_source_v40 as qualification

ROOT = Path(__file__).resolve().parents[3]


class CurrentWorkspaceSourceQualificationV40Tests(unittest.TestCase):
    def test_historical_qualification_uses_frozen_git_state(self) -> None:
        result = qualification.verify(ROOT)
        self.assertEqual(
            result["qualification_id"], "p17.current-workspace-source.v40.20260910"
        )
        self.assertFalse(result["mutable_worktree_sources_read"])

    def test_exact_source_counts_and_overlap_are_preserved(self) -> None:
        result = qualification.verify(ROOT)
        self.assertEqual(result["implementation_source_count"], 9)
        self.assertEqual(result["source_successor_count"], 28)
        self.assertEqual(result["guard_source_count"], 3)
        self.assertEqual(result["intentional_overlap"], ["Cargo.lock"])

    def test_runtime_and_product_claims_remain_false(self) -> None:
        result = qualification.verify(ROOT)
        self.assertFalse(result["actual_hangul"])
        self.assertFalse(result["production"])
        self.assertFalse(result["product_complete"])
        self.assertFalse(result["receipt_blob_verified"])


if __name__ == "__main__":
    unittest.main()
