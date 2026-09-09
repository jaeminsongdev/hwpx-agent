from __future__ import annotations

import copy
import unittest

from tools.p17 import current_workspace_source_qualification_v24 as qualification
from tools.p17 import frozen_current_source_history_v1 as history


class CurrentWorkspaceSourceQualificationV24Tests(unittest.TestCase):
    def test_current_qualification_verifies(self) -> None:
        contract = history.verify_version(qualification.ROOT, 24)
        self.assertEqual(
            contract["qualification_id"],
            "p17.current-workspace-source.v24.20260907",
        )
        self.assertTrue(contract["claims"]["p06_table_cell_style_v1_sources_bound"])
        self.assertFalse(contract["claims"]["p06_04_complete"])
        self.assertFalse(contract["claims"]["actual_hangul"])

    def test_implementation_sources_are_unique_and_complete(self) -> None:
        paths = [entry["path"] for entry in qualification.IMPLEMENTATION_SOURCES]
        self.assertEqual(len(paths), len(set(paths)))
        self.assertEqual(len(paths), 10)
        self.assertIn("crates/hwpx-package/src/table_cell_style.rs", paths)
        self.assertIn(
            "crates/hwpx-package/examples/p06_04_table_cell_style_target_fixture.rs",
            paths,
        )
        self.assertIn("protocol/private/p06-table-cell-style-v1.json", paths)
        self.assertIn(
            "implementation/p06/tools/create-hancom-2020-table-source.ps1", paths
        )
        self.assertNotIn("tools/p01/run_ci.py", paths)

    def test_predecessor_is_exact_v23_contract(self) -> None:
        qualification.validate_predecessor(qualification.ROOT)
        self.assertEqual(
            qualification.PREVIOUS_QUALIFICATION[1],
            "62ed365ab62c367f4c25483a53333c185d34bfcbca09aa60d695da5780184aff",
        )

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
