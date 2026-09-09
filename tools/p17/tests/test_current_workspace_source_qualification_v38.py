from __future__ import annotations

import copy
import unittest

from tools.p17 import current_workspace_source_qualification_v38 as qualification
from tools.p17 import frozen_current_source_history_v1 as history


class CurrentWorkspaceSourceQualificationV38Tests(unittest.TestCase):
    def test_current_qualification_verifies(self) -> None:
        contract = history.verify_version(qualification.ROOT, 38)
        self.assertEqual(
            contract["qualification_id"], "p17.current-workspace-source.v38.20260907"
        )
        claims = contract["claims"]
        self.assertTrue(claims["p06_06_formula_id_profile_source_bound"])
        self.assertTrue(claims["p06_06_structural_target_source_bound"])
        self.assertTrue(claims["p06_06_target_oracle_checker_source_bound"])
        self.assertTrue(claims["p06_06_target_access_diagnostics_source_bound"])
        self.assertFalse(claims["p06_06_structural_differential_verified"])
        self.assertFalse(claims["p06_06_product_target_oracle_verified"])
        self.assertFalse(claims["p06_06_complete"])
        self.assertFalse(claims["actual_hangul"])

    def test_implementation_sources_are_unique_and_complete(self) -> None:
        paths = [entry["path"] for entry in qualification.IMPLEMENTATION_SOURCES]
        self.assertEqual(len(paths), len(set(paths)))
        self.assertEqual(len(paths), 9)
        self.assertIn("crates/hwpx-package/src/id_index.rs", paths)
        self.assertIn(
            "crates/hwpx-package/examples/"
            "p06_06_table_formula_structural_target_fixture.rs",
            paths,
        )
        self.assertIn(
            "crates/hwpx-package/examples/p06_06_table_formula_target_oracle.rs", paths
        )
        self.assertIn("implementation/p06/P06-06_TARGET_ATTEMPTS_DIAGNOSTIC.md", paths)

    def test_predecessor_is_exact_v37_contract(self) -> None:
        qualification.validate_predecessor(qualification.ROOT)
        self.assertEqual(
            qualification.PREVIOUS_QUALIFICATION[1],
            "f254ed93256a578539a95d64bb425ab29d5cc0af8b0c4d7406d09c02895cefa8",
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
