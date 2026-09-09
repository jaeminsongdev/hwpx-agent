from __future__ import annotations

import copy
import unittest

from tools.p17 import current_workspace_source_qualification_v26 as qualification
from tools.p17 import frozen_current_source_history_v1 as history


class CurrentWorkspaceSourceQualificationV26Tests(unittest.TestCase):
    def test_current_qualification_verifies(self) -> None:
        contract = history.verify_version(qualification.ROOT, 26)
        self.assertEqual(
            contract["qualification_id"],
            "p17.current-workspace-source.v26.20260907",
        )
        self.assertTrue(
            contract["claims"]["p06_table_source_text_digest_canonicalized"]
        )
        self.assertFalse(contract["claims"]["p06_04_complete"])
        self.assertFalse(contract["claims"]["actual_hangul"])

    def test_implementation_sources_are_unique_and_complete(self) -> None:
        paths = [entry["path"] for entry in qualification.IMPLEMENTATION_SOURCES]
        self.assertEqual(len(paths), len(set(paths)))
        self.assertEqual(len(paths), 3)
        self.assertIn(
            "implementation/p06/tools/create-hancom-2020-table-source.ps1", paths
        )
        self.assertIn("tools/p06/validate_table_cell_style_contract.py", paths)
        self.assertIn("tools/p06/tests/test_table_cell_style_contract.py", paths)
        self.assertNotIn("tools/p01/run_ci.py", paths)

    def test_predecessor_is_exact_v25_contract(self) -> None:
        qualification.validate_predecessor(qualification.ROOT)
        self.assertEqual(
            qualification.PREVIOUS_QUALIFICATION[1],
            "408c8531ed2775f45cb13f20f65edf1eead6ac4363cf5201c9e0589aba671393",
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
