from __future__ import annotations

from pathlib import Path
import unittest

from tools.p17 import frozen_current_source_v39 as qualification

ROOT = Path(__file__).resolve().parents[3]


class CurrentWorkspaceSourceQualificationV39Tests(unittest.TestCase):
    def test_historical_qualification_uses_frozen_git_state(self) -> None:
        result = qualification.verify(ROOT)
        self.assertEqual(
            result["qualification_id"], "p17.current-workspace-source.v39.20260908"
        )
        self.assertFalse(result["mutable_worktree_sources_read"])

    def test_exact_source_counts_are_preserved(self) -> None:
        result = qualification.verify(ROOT)
        self.assertEqual(result["implementation_source_count"], 7)
        self.assertEqual(result["source_successor_count"], 26)
        self.assertEqual(result["guard_source_count"], 3)

    def test_runtime_and_product_claims_remain_false(self) -> None:
        result = qualification.verify(ROOT)
        self.assertFalse(result["actual_hangul"])
        self.assertFalse(result["production"])
        self.assertFalse(result["product_complete"])
        self.assertFalse(result["receipt_blob_verified"])


if __name__ == "__main__":
    unittest.main()
