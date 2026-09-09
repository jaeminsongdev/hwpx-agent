from __future__ import annotations

import copy
import unittest

from tools.p17 import current_workspace_source_qualification_v31 as qualification
from tools.p17 import frozen_current_source_history_v1 as history


class CurrentWorkspaceSourceQualificationV31Tests(unittest.TestCase):
    def test_current_qualification_verifies(self) -> None:
        contract = history.verify_version(qualification.ROOT, 31)
        self.assertEqual(
            contract["qualification_id"],
            "p17.current-workspace-source.v31.20260907",
        )
        claims = contract["claims"]
        self.assertTrue(claims["p06_06_formula_ast_core_bound"])
        self.assertTrue(claims["p06_06_row_column_reference_transform_bound"])
        self.assertTrue(claims["p06_06_exact_grid_formula_cell_readback_bound"])
        self.assertFalse(claims["p06_06_formula_evaluation_verified"])
        self.assertFalse(claims["p06_06_oracle_cache_verified"])
        self.assertFalse(claims["p06_06_hwpx_lowering_verified"])
        self.assertFalse(claims["p06_06_hancom_2020_oracle_verified"])
        self.assertFalse(claims["p06_06_complete"])

    def test_implementation_sources_are_unique_and_complete(self) -> None:
        paths = [entry["path"] for entry in qualification.IMPLEMENTATION_SOURCES]
        self.assertEqual(len(paths), len(set(paths)))
        self.assertEqual(len(paths), 8)
        self.assertIn("crates/domain-ir/src/table_formula.rs", paths)
        self.assertIn("crates/domain-ir/tests/table_formula.rs", paths)
        self.assertIn("protocol/private/p06-table-formula-v1.json", paths)
        self.assertIn("protocol/migrations/p06-table-formula-v0-to-v1.md", paths)

    def test_predecessor_is_exact_v30_contract(self) -> None:
        qualification.validate_predecessor(qualification.ROOT)
        self.assertEqual(
            qualification.PREVIOUS_QUALIFICATION[1],
            "fe4523ca2141f99574566ff0197e4ac465c5cadc8e4397ca7276854d84e27357",
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
