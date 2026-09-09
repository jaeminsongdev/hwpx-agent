from __future__ import annotations

import copy
import unittest

from tools.p17 import current_workspace_source_qualification_v25 as qualification
from tools.p17 import frozen_current_source_history_v1 as history


class CurrentWorkspaceSourceQualificationV25Tests(unittest.TestCase):
    def test_current_qualification_verifies(self) -> None:
        contract = history.verify_version(qualification.ROOT, 25)
        self.assertEqual(
            contract["qualification_id"],
            "p17.current-workspace-source.v25.20260907",
        )
        self.assertTrue(
            contract["claims"]["p06_table_cell_style_runtime_readback_sources_bound"]
        )
        self.assertFalse(contract["claims"]["p06_04_complete"])
        self.assertFalse(contract["claims"]["actual_hangul"])

    def test_implementation_sources_are_unique_and_complete(self) -> None:
        paths = [entry["path"] for entry in qualification.IMPLEMENTATION_SOURCES]
        self.assertEqual(len(paths), len(set(paths)))
        self.assertEqual(len(paths), 6)
        self.assertIn(
            "implementation/p06/tools/run-hancom-2020-cell-style-readback.ps1",
            paths,
        )
        self.assertIn(
            "implementation/p06/tests/Test-Hancom2020CellStyleReadback.ps1", paths
        )
        self.assertIn("protocol/private/p06-table-cell-style-v1.json", paths)
        self.assertNotIn("tools/p01/run_ci.py", paths)

    def test_predecessor_is_exact_v24_contract(self) -> None:
        qualification.validate_predecessor(qualification.ROOT)
        self.assertEqual(
            qualification.PREVIOUS_QUALIFICATION[1],
            "02e12717738bf70bf76ea69da516a583ed06901ed294700c3853e9b0f84e3d19",
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
