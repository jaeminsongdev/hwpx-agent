from __future__ import annotations

import copy
import unittest

from tools.p17 import current_workspace_source_qualification_v34 as qualification
from tools.p17 import frozen_current_source_history_v1 as history


class CurrentWorkspaceSourceQualificationV34Tests(unittest.TestCase):
    def test_current_qualification_verifies(self) -> None:
        contract = history.verify_version(qualification.ROOT, 34)
        self.assertEqual(
            contract["qualification_id"],
            "p17.current-workspace-source.v34.20260907",
        )
        claims = contract["claims"]
        self.assertTrue(claims["p06_05_table_layout_hwpx_profile_v2_bound"])
        self.assertTrue(claims["p06_05_inner_margin_typed_and_bounded"])
        self.assertTrue(claims["p06_05_font_metric_target_builder_bound"])
        self.assertTrue(claims["p06_05_bounded_hancom_readback_wrapper_bound"])
        self.assertFalse(claims["p06_05_actual_target_hancom_readback_verified"])
        self.assertFalse(claims["p06_05_complete"])

    def test_implementation_sources_are_unique_and_complete(self) -> None:
        paths = [entry["path"] for entry in qualification.IMPLEMENTATION_SOURCES]
        self.assertEqual(len(paths), len(set(paths)))
        self.assertEqual(len(paths), 15)
        self.assertIn("crates/hwpx-package/src/table_layout.rs", paths)
        self.assertIn("protocol/private/p06-table-layout-hwpx-v2.json", paths)
        self.assertIn("tools/p06/validate_table_layout_hwpx_v2_contract.py", paths)
        self.assertIn("implementation/p06/P06-04_TARGET_READBACK_REPORT.md", paths)

    def test_predecessor_is_exact_v33_contract(self) -> None:
        qualification.validate_predecessor(qualification.ROOT)
        self.assertEqual(
            qualification.PREVIOUS_QUALIFICATION[1],
            "329c111bdce1a401e4b221341d5295e4b730c6bb3b917ebd6fb6a201affab297",
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
