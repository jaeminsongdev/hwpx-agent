from __future__ import annotations

import copy
import unittest

from tools.p17 import current_workspace_source_qualification_v23 as qualification


class CurrentWorkspaceSourceQualificationV23Tests(unittest.TestCase):
    def test_current_qualification_verifies(self) -> None:
        contract = qualification.verify()
        self.assertEqual(
            contract["qualification_id"],
            "p17.current-workspace-source.v23.20260907",
        )
        self.assertTrue(contract["claims"]["p06_table_merge_split_v1_sources_bound"])
        self.assertFalse(contract["claims"]["p06_03_complete"])

    def test_implementation_sources_are_unique_and_complete(self) -> None:
        paths = [entry["path"] for entry in qualification.IMPLEMENTATION_SOURCES]
        self.assertEqual(len(paths), len(set(paths)))
        self.assertEqual(len(paths), 8)
        self.assertIn("crates/domain-ir/src/table_merge_split.rs", paths)
        self.assertIn("protocol/private/p06-table-merge-split-v1.json", paths)
        self.assertIn("tools/p06/validate_table_merge_split_contract.py", paths)
        self.assertNotIn("tools/p01/run_ci.py", paths)

    def test_predecessor_is_exact_v22_contract(self) -> None:
        qualification.validate_predecessor(qualification.ROOT)
        self.assertEqual(
            qualification.PREVIOUS_QUALIFICATION[1],
            "2d52898b8d232ea819f4f875a3760ba676dc7d67899f78687987014cead3e176",
        )

    def test_receipt_claim_drift_fails_closed(self) -> None:
        receipt = qualification.foundation.load_document(
            qualification.receipt_path(qualification.ROOT), "receipt"
        )
        mutated = copy.deepcopy(receipt)
        mutated["phase_complete"] = True
        with self.assertRaises(qualification.foundation.QualificationError):
            qualification.validate_receipt(mutated)


if __name__ == "__main__":
    unittest.main()
