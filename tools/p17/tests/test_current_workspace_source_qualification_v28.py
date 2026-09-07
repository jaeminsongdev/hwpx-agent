from __future__ import annotations

import copy
import unittest

from tools.p17 import current_workspace_source_qualification_v28 as qualification


class CurrentWorkspaceSourceQualificationV28Tests(unittest.TestCase):
    def test_current_qualification_verifies(self) -> None:
        contract = qualification.verify()
        self.assertEqual(
            contract["qualification_id"],
            "p17.current-workspace-source.v28.20260907",
        )
        self.assertTrue(contract["claims"]["p06_table_layout_hwpx_component_bound"])
        self.assertFalse(contract["claims"]["p06_04_complete"])
        self.assertFalse(contract["claims"]["p06_05_complete"])
        self.assertFalse(contract["claims"]["actual_hangul"])

    def test_implementation_sources_are_unique_and_complete(self) -> None:
        paths = [entry["path"] for entry in qualification.IMPLEMENTATION_SOURCES]
        self.assertEqual(len(paths), len(set(paths)))
        self.assertEqual(len(paths), 10)
        self.assertIn("Cargo.lock", paths)
        self.assertIn("crates/hwpx-package/Cargo.toml", paths)
        self.assertIn("crates/hwpx-package/src/table_layout.rs", paths)
        self.assertIn("crates/hwpx-package/tests/table_layout.rs", paths)
        self.assertIn("protocol/private/p06-table-layout-hwpx-v1.json", paths)
        self.assertIn("tools/p06/validate_table_layout_hwpx_contract.py", paths)
        self.assertNotIn("tools/p01/run_ci.py", paths)

    def test_predecessor_is_exact_v27_contract(self) -> None:
        qualification.validate_predecessor(qualification.ROOT)
        self.assertEqual(
            qualification.PREVIOUS_QUALIFICATION[1],
            "eb2ca5b661ed303ba9522e401b732606621c2b63c32eaf5f2dfb8ddf6563a222",
        )

    def test_only_lock_and_package_manifest_advance_the_successor_set(self) -> None:
        prior = {entry["path"]: entry for entry in qualification.foundation.SUCCESSORS}
        current = {entry["path"]: entry for entry in qualification.SUCCESSORS}
        self.assertEqual(set(current) - set(prior), {"crates/hwpx-package/Cargo.toml"})
        self.assertEqual(
            {path for path in prior if prior[path] != current[path]},
            {"Cargo.lock"},
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
