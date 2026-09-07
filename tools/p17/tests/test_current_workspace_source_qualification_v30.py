from __future__ import annotations

import copy
import unittest

from tools.p17 import current_workspace_source_qualification_v30 as qualification


class CurrentWorkspaceSourceQualificationV30Tests(unittest.TestCase):
    def test_current_qualification_verifies(self) -> None:
        contract = qualification.verify()
        self.assertEqual(
            contract["qualification_id"],
            "p17.current-workspace-source.v30.20260907",
        )
        self.assertTrue(contract["claims"]["p06_04_active_document_fix_bound"])
        self.assertTrue(contract["claims"]["p06_04_pre_save_marker_gate_bound"])
        self.assertFalse(contract["claims"]["diagnostic_attempt03_pass"])
        self.assertFalse(contract["claims"]["actual_hangul_retry"])
        self.assertFalse(contract["claims"]["p06_04_complete"])

    def test_implementation_sources_are_unique_and_complete(self) -> None:
        paths = [entry["path"] for entry in qualification.IMPLEMENTATION_SOURCES]
        self.assertEqual(len(paths), len(set(paths)))
        self.assertEqual(len(paths), 5)
        self.assertIn("implementation/p06/tools/create-hancom-2020-table-source.ps1", paths)
        self.assertIn("implementation/p06/tests/Test-Hancom2020CellStyleReadback.ps1", paths)
        self.assertIn("protocol/private/p06-table-cell-style-v1.json", paths)

    def test_predecessor_is_exact_v29_contract(self) -> None:
        qualification.validate_predecessor(qualification.ROOT)
        self.assertEqual(
            qualification.PREVIOUS_QUALIFICATION[1],
            "bf18ccec5be200cda7a4c00cabe68741adf0e5c01a38d6977bb570fa88299876",
        )

    def test_successor_set_is_exactly_preserved(self) -> None:
        self.assertEqual(qualification.SUCCESSORS, qualification.predecessor.SUCCESSORS)
        self.assertEqual(len(qualification.SUCCESSORS), 26)

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
