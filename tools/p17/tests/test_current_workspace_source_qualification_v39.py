from __future__ import annotations

import copy
import unittest

from tools.p17 import current_workspace_source_qualification_v39 as qualification


class CurrentWorkspaceSourceQualificationV39Tests(unittest.TestCase):
    def test_current_qualification_verifies(self) -> None:
        contract = qualification.verify()
        self.assertEqual(
            contract["qualification_id"], "p17.current-workspace-source.v39.20260908"
        )
        claims = contract["claims"]
        self.assertTrue(claims["p06_06_target_v2_contract_source_bound"])
        self.assertTrue(claims["p06_06_target_v2_validator_source_bound"])
        self.assertTrue(claims["p06_06_target_v2_tamper_tests_source_bound"])
        self.assertTrue(claims["p06_06_completion_report_source_bound"])
        self.assertTrue(claims["p06_06_actual_oracle_hashes_source_bound"])
        self.assertFalse(claims["p06_06_structural_differential_verified"])
        self.assertFalse(claims["p06_06_product_target_oracle_verified"])
        self.assertFalse(claims["p06_06_complete"])
        self.assertFalse(claims["actual_hangul"])

    def test_implementation_sources_are_unique_and_complete(self) -> None:
        paths = [entry["path"] for entry in qualification.IMPLEMENTATION_SOURCES]
        self.assertEqual(len(paths), len(set(paths)))
        self.assertEqual(len(paths), 7)
        self.assertIn("protocol/private/p06-table-formula-target-v2.json", paths)
        self.assertIn("tools/p06/validate_table_formula_target_v2_contract.py", paths)
        self.assertIn("tools/p06/tests/test_table_formula_target_v2_contract.py", paths)
        self.assertIn("implementation/p06/P06-06_TARGET_READBACK_REPORT.md", paths)

    def test_predecessor_is_exact_v38_contract(self) -> None:
        qualification.validate_predecessor(qualification.ROOT)
        self.assertEqual(
            qualification.PREVIOUS_QUALIFICATION[1],
            "818e41c4e8ee46eea3b0f31b7d769eb56d19f9de46310ed73e37285cb237ebe0",
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
