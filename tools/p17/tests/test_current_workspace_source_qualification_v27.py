from __future__ import annotations

import copy
import unittest

from tools.p17 import current_workspace_source_qualification_v27 as qualification
from tools.p17 import frozen_current_source_history_v1 as history


class CurrentWorkspaceSourceQualificationV27Tests(unittest.TestCase):
    def test_current_qualification_verifies(self) -> None:
        contract = history.verify_version(qualification.ROOT, 27)
        self.assertEqual(
            contract["qualification_id"],
            "p17.current-workspace-source.v27.20260907",
        )
        self.assertTrue(contract["claims"]["p06_table_layout_solver_component_bound"])
        self.assertFalse(contract["claims"]["p06_04_complete"])
        self.assertFalse(contract["claims"]["p06_05_complete"])
        self.assertFalse(contract["claims"]["actual_hangul"])

    def test_implementation_sources_are_unique_and_complete(self) -> None:
        paths = [entry["path"] for entry in qualification.IMPLEMENTATION_SOURCES]
        self.assertEqual(len(paths), len(set(paths)))
        self.assertEqual(len(paths), 8)
        self.assertIn("crates/domain-ir/src/table_layout.rs", paths)
        self.assertIn("crates/domain-ir/tests/table_layout.rs", paths)
        self.assertIn("protocol/private/p06-table-layout-v1.json", paths)
        self.assertIn("tools/p06/validate_table_layout_contract.py", paths)
        self.assertNotIn("tools/p01/run_ci.py", paths)

    def test_predecessor_is_exact_v26_contract(self) -> None:
        qualification.validate_predecessor(qualification.ROOT)
        self.assertEqual(
            qualification.PREVIOUS_QUALIFICATION[1],
            "60867a4ab87dbec6327610cfd4d682826d35368c606ea736867012aa970749d1",
        )

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
