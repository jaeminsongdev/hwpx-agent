from __future__ import annotations

import copy
import unittest

from tools.p17 import current_workspace_source_qualification_v36 as qualification


class CurrentWorkspaceSourceQualificationV36Tests(unittest.TestCase):
    def test_current_qualification_verifies(self) -> None:
        contract = qualification.verify()
        self.assertEqual(
            contract["qualification_id"], "p17.current-workspace-source.v36.20260907"
        )
        claims = contract["claims"]
        self.assertTrue(claims["p06_05_calibrated_target_builder_bound"])
        self.assertTrue(claims["p06_05_product_target_contract_v2_bound"])
        self.assertTrue(claims["p06_05_calibration_history_hashes_source_bound"])
        self.assertTrue(claims["p06_05_actual_oracle_hashes_source_bound"])
        self.assertTrue(claims["p06_05_target_v2_validator_source_bound"])
        self.assertFalse(claims["p06_05_actual_target_hancom_readback_verified"])
        self.assertFalse(claims["p06_05_complete"])
        self.assertFalse(claims["actual_hangul"])

    def test_implementation_sources_are_unique_and_complete(self) -> None:
        paths = [entry["path"] for entry in qualification.IMPLEMENTATION_SOURCES]
        self.assertEqual(len(paths), len(set(paths)))
        self.assertEqual(len(paths), 6)
        self.assertIn("protocol/private/p06-table-layout-target-v2.json", paths)
        self.assertIn("tools/p06/validate_table_layout_target_v2_contract.py", paths)
        self.assertIn("implementation/p06/P06-05_TARGET_READBACK_REPORT.md", paths)

    def test_predecessor_is_exact_v35_contract(self) -> None:
        qualification.validate_predecessor(qualification.ROOT)
        self.assertEqual(
            qualification.PREVIOUS_QUALIFICATION[1],
            "37a2b79a528cb90b59482286ab7835674e34e2f08dddfed0c71a99dcecec72a1",
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
