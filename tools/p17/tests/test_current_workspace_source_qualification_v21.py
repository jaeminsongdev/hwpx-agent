from __future__ import annotations

import copy
import unittest

from tools.p17 import current_workspace_source_qualification_v21 as qualification


class CurrentWorkspaceSourceQualificationV21Tests(unittest.TestCase):
    def test_current_qualification_verifies(self) -> None:
        contract = qualification.verify()
        self.assertEqual(
            contract["qualification_id"],
            "p17.current-workspace-source.v21.20260907",
        )
        self.assertTrue(contract["claims"]["p06_table_grid_v1_sources_bound"])
        self.assertFalse(contract["claims"]["p06_01_complete"])

    def test_implementation_sources_are_unique_and_complete(self) -> None:
        paths = [entry["path"] for entry in qualification.IMPLEMENTATION_SOURCES]
        self.assertEqual(len(paths), len(set(paths)))
        self.assertEqual(len(paths), 8)
        self.assertIn("crates/domain-ir/src/table_grid.rs", paths)
        self.assertIn("protocol/private/p06-table-grid-v1.json", paths)
        self.assertIn("tools/p06/validate_table_grid_contract.py", paths)
        self.assertNotIn("tools/p01/run_ci.py", paths)

    def test_receipt_claim_drift_fails_closed(self) -> None:
        receipt = qualification.predecessor.load_document(
            qualification.receipt_path(qualification.ROOT), "receipt"
        )
        mutated = copy.deepcopy(receipt)
        mutated["phase_complete"] = True
        with self.assertRaises(qualification.predecessor.QualificationError):
            qualification.validate_receipt(mutated)


if __name__ == "__main__":
    unittest.main()
