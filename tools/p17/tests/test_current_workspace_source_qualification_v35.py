from __future__ import annotations

import copy
import unittest

from tools.p17 import current_workspace_source_qualification_v35 as qualification
from tools.p17 import frozen_current_source_history_v1 as history


class CurrentWorkspaceSourceQualificationV35Tests(unittest.TestCase):
    def test_current_qualification_verifies(self) -> None:
        contract = history.verify_version(qualification.ROOT, 35)
        self.assertEqual(
            contract["qualification_id"],
            "p17.current-workspace-source.v35.20260907",
        )
        claims = contract["claims"]
        self.assertTrue(claims["p06_05_target_builder_v2_bound"])
        self.assertTrue(claims["p06_05_stale_layout_cache_invalidation_bound"])
        self.assertTrue(claims["p06_05_product_target_contract_v1_bound"])
        self.assertTrue(claims["p06_05_attempt01_failed_open_diagnostic_bound"])
        self.assertFalse(claims["p06_05_actual_target_hancom_readback_verified"])
        self.assertFalse(claims["p06_05_complete"])

    def test_implementation_sources_are_unique_and_complete(self) -> None:
        paths = [entry["path"] for entry in qualification.IMPLEMENTATION_SOURCES]
        self.assertEqual(len(paths), len(set(paths)))
        self.assertEqual(len(paths), 8)
        self.assertIn("protocol/private/p06-table-layout-target-v1.json", paths)
        self.assertIn("tools/p06/validate_table_layout_target_contract.py", paths)
        self.assertIn("implementation/p06/P06-05_TARGET_ATTEMPT01_DIAGNOSTIC.md", paths)

    def test_predecessor_is_exact_v34_contract(self) -> None:
        qualification.validate_predecessor(qualification.ROOT)
        self.assertEqual(
            qualification.PREVIOUS_QUALIFICATION[1],
            "7bdd50caf207f8c25f10721d7aa930b465834ae48f97ca4471281bb081bb1a12",
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
