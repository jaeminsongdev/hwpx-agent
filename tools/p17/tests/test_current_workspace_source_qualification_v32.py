from __future__ import annotations

import copy
import unittest

from tools.p17 import current_workspace_source_qualification_v32 as qualification


class CurrentWorkspaceSourceQualificationV32Tests(unittest.TestCase):
    def test_current_qualification_verifies(self) -> None:
        contract = qualification.verify()
        self.assertEqual(
            contract["qualification_id"],
            "p17.current-workspace-source.v32.20260907",
        )
        claims = contract["claims"]
        self.assertTrue(claims["p06_06_formula_source_capture_tooling_bound"])
        self.assertTrue(claims["p06_06_exact_hancom_2020_identity_guard_bound"])
        self.assertTrue(claims["p06_06_bounded_watchdog_and_progress_bound"])
        self.assertTrue(claims["p06_06_hancom_authored_formula_action_bound"])
        self.assertFalse(claims["p06_06_formula_source_capture_executed"])
        self.assertFalse(claims["p06_06_formula_field_shape_verified"])
        self.assertFalse(claims["p06_06_hancom_2020_oracle_verified"])
        self.assertFalse(claims["p06_06_complete"])

    def test_implementation_sources_are_unique_and_complete(self) -> None:
        paths = [entry["path"] for entry in qualification.IMPLEMENTATION_SOURCES]
        self.assertEqual(len(paths), len(set(paths)))
        self.assertEqual(len(paths), 4)
        self.assertIn(
            "implementation/p06/tools/create-hancom-2020-formula-source.ps1", paths
        )
        self.assertIn(
            "implementation/p06/tools/run-hancom-2020-formula-source.ps1", paths
        )
        self.assertIn(
            "implementation/p06/tests/Test-Hancom2020FormulaSource.ps1", paths
        )

    def test_predecessor_is_exact_v31_contract(self) -> None:
        qualification.validate_predecessor(qualification.ROOT)
        self.assertEqual(
            qualification.PREVIOUS_QUALIFICATION[1],
            "dcda4b3ea4a8c8d5ce858ef1cb7054c1f3730a8b4be49fd322841a754f75dec7",
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
