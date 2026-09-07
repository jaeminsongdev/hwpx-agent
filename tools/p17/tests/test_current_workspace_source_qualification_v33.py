from __future__ import annotations

import copy
import unittest

from tools.p17 import current_workspace_source_qualification_v33 as qualification


class CurrentWorkspaceSourceQualificationV33Tests(unittest.TestCase):
    def test_current_qualification_verifies(self) -> None:
        contract = qualification.verify()
        self.assertEqual(
            contract["qualification_id"],
            "p17.current-workspace-source.v33.20260907",
        )
        claims = contract["claims"]
        self.assertTrue(claims["p06_04_preservation_preview_profile_v2_bound"])
        self.assertTrue(claims["p06_04_table_id_profile_v2_bound"])
        self.assertTrue(claims["p06_04_cell_style_profile_v2_bound"])
        self.assertTrue(claims["p06_04_v1_default_behavior_preserved"])
        self.assertFalse(claims["p06_04_actual_source_capture_evidence_bound"])
        self.assertFalse(claims["p06_04_product_target_hancom_readback_verified"])
        self.assertFalse(claims["p06_04_complete"])

    def test_implementation_sources_are_unique_and_complete(self) -> None:
        paths = [entry["path"] for entry in qualification.IMPLEMENTATION_SOURCES]
        self.assertEqual(len(paths), len(set(paths)))
        self.assertEqual(len(paths), 14)
        self.assertIn("crates/hwpx-package/src/preservation.rs", paths)
        self.assertIn("crates/hwpx-package/src/id_index.rs", paths)
        self.assertIn("crates/hwpx-package/src/table_cell_style.rs", paths)
        self.assertIn("protocol/private/p06-table-cell-style-v2.json", paths)
        self.assertIn("tools/p06/validate_table_cell_style_v2_contract.py", paths)

    def test_predecessor_is_exact_v32_contract(self) -> None:
        qualification.validate_predecessor(qualification.ROOT)
        self.assertEqual(
            qualification.PREVIOUS_QUALIFICATION[1],
            "e386ea8ab4e390c14356c875529765064900d405ca7737bb8f6f2ff509f0e16f",
        )

    def test_successor_set_is_exactly_preserved(self) -> None:
        self.assertEqual(qualification.SUCCESSORS, qualification.predecessor.SUCCESSORS)
        self.assertEqual(len(qualification.SUCCESSORS), 26)

    def test_receipt_claim_drift_fails_closed(self) -> None:
        receipt = qualification.foundation.load_document(
            qualification.receipt_path(qualification.ROOT), "receipt"
        )
        mutated = copy.deepcopy(receipt)
        mutated["actual_hangul"] = True
        with self.assertRaises(qualification.foundation.QualificationError):
            qualification.validate_receipt(mutated)


if __name__ == "__main__":
    unittest.main()
