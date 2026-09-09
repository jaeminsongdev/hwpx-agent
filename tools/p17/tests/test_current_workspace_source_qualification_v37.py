from __future__ import annotations

import copy
import unittest

from tools.p17 import current_workspace_source_qualification_v37 as qualification
from tools.p17 import frozen_current_source_history_v1 as history


class CurrentWorkspaceSourceQualificationV37Tests(unittest.TestCase):
    def test_current_qualification_verifies(self) -> None:
        contract = history.verify_version(qualification.ROOT, 37)
        self.assertEqual(
            contract["qualification_id"], "p17.current-workspace-source.v37.20260907"
        )
        claims = contract["claims"]
        self.assertTrue(claims["p06_06_hwpx_adapter_source_bound"])
        self.assertTrue(claims["p06_06_actual_source_evidence_hashes_bound"])
        self.assertTrue(claims["p06_06_adapter_contract_validator_source_bound"])
        self.assertFalse(claims["p06_06_actual_source_capture_verified"])
        self.assertFalse(claims["p06_06_actual_source_adapter_readback_verified"])
        self.assertFalse(claims["p06_06_product_target_oracle_verified"])
        self.assertFalse(claims["p06_06_complete"])
        self.assertFalse(claims["actual_hangul"])

    def test_implementation_sources_are_unique_and_complete(self) -> None:
        paths = [entry["path"] for entry in qualification.IMPLEMENTATION_SOURCES]
        self.assertEqual(len(paths), len(set(paths)))
        self.assertEqual(len(paths), 9)
        self.assertIn("crates/hwpx-package/src/table_formula.rs", paths)
        self.assertIn("protocol/private/p06-table-formula-hwpx-v1.json", paths)
        self.assertIn("tools/p06/validate_table_formula_hwpx_contract.py", paths)

    def test_predecessor_is_exact_v36_contract(self) -> None:
        qualification.validate_predecessor(qualification.ROOT)
        self.assertEqual(
            qualification.PREVIOUS_QUALIFICATION[1],
            "9758f4510a17459e28667aacbe729ee43336729218dea9343dc57dd11c5138ab",
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
