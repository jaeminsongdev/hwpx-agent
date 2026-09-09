from __future__ import annotations

import copy
import unittest

from tools.p17 import current_workspace_source_qualification_v29 as qualification
from tools.p17 import frozen_current_source_history_v1 as history


class CurrentWorkspaceSourceQualificationV29Tests(unittest.TestCase):
    def test_current_qualification_verifies(self) -> None:
        contract = history.verify_version(qualification.ROOT, 29)
        self.assertEqual(
            contract["qualification_id"],
            "p17.current-workspace-source.v29.20260907",
        )
        self.assertTrue(contract["claims"]["p06_current_font_metric_component_bound"])
        self.assertTrue(
            contract["claims"]["actual_current_pc_installed_font_measurement"]
        )
        self.assertFalse(contract["claims"]["actual_hangul_renderer"])
        self.assertFalse(contract["claims"]["p06_05_complete"])

    def test_implementation_sources_are_unique_and_complete(self) -> None:
        paths = [entry["path"] for entry in qualification.IMPLEMENTATION_SOURCES]
        self.assertEqual(len(paths), len(set(paths)))
        self.assertEqual(len(paths), 15)
        self.assertIn("crates/hwpx-package/src/font_metric_receipt.rs", paths)
        self.assertIn("crates/hwpx-package/tests/font_metric_receipt.rs", paths)
        self.assertIn(
            "implementation/p06/tools/measure-hancom-2020-layout-font.ps1", paths
        )
        self.assertIn("protocol/private/p06-font-metric-receipt-v1.json", paths)
        self.assertIn("tools/p17/run_current_workspace_source_checks.py", paths)
        self.assertNotIn("artifacts/p06/font-metric-runs", paths)

    def test_predecessor_is_exact_v28_contract(self) -> None:
        qualification.validate_predecessor(qualification.ROOT)
        self.assertEqual(
            qualification.PREVIOUS_QUALIFICATION[1],
            "55fb75ca03e7331b246d3cc309df84455fa0a32b087a23b73bc7b24ad011091e",
        )

    def test_only_hwpx_manifest_advances_the_successor_set(self) -> None:
        prior = {entry["path"]: entry for entry in qualification.predecessor.SUCCESSORS}
        current = {entry["path"]: entry for entry in qualification.SUCCESSORS}
        self.assertEqual(set(current), set(prior))
        self.assertEqual(
            {path for path in prior if prior[path] != current[path]},
            {"crates/hwpx-package/Cargo.toml"},
        )
        self.assertEqual(len(current), 26)

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
