"""Physical source ancestry and fail-closed inventories; not native/SQL/Gate."""
import copy
import importlib.util
import json
import unittest
from pathlib import Path
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location("p114_bytes", Path(__file__).parents[1] / "verify_stored_formula_compiler_progress.py")
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)

class StoredFormulaCompilerProgressTests(unittest.TestCase):
    def data(self):
        groups = {"source_delta": M.PARENTS + M.NEW_SOURCES, "source_archives_added": M.ARCHIVES,
                  "predecessor_receipts_added": M.PREDECESSORS, "current_executables": M.EXECUTABLES}
        data = {key: [{"path": path, "bytes": 1, "sha256": "0"*64} for path in paths] for key, paths in groups.items()}
        data.update({"inherited_checkpoint": {"path": M.PREVIOUS}, "current_source_files_count": 1021,
                     "qualification": {key: False for key in M.FALSE_QUALIFICATIONS},
                     "P09_gate": "OPEN", "P10_new_implementation": False, "product_complete": False,
                     "remaining_coarse_groups_minimum": 6, "remaining_coarse_groups_closed_by_slice": 0})
        data["qualification"]["actual_source_original_compiler_binding_verified"] = True
        return data
    def check(self, data):
        with patch.object(M.BASE, "exact", return_value=True):
            return M.verify_current_manifest(data, {"previous_checkpoint": {"path": M.PREVIOUS}})
    def test_whole_two_parent_preimages_and_inverse_retain_all_original_bytes(self):
        self.assertEqual(len(M.original_sources()), 1009)
        for path in M.PARENTS:
            raw = (M.ROOT / path).read_bytes()
            archived = (M.ROOT / (M.ARCHIVE + path)).read_bytes()
            self.assertEqual(M.restored_parent(path, raw), archived)
            self.assertNotEqual(M.restored_parent(path, raw+b"\nUNDECLARED"), archived)
            with self.assertRaises(ValueError): M.restored_parent(path, archived)
            with self.assertRaises(ValueError): M.restored_parent(path, raw+M.EDITS[path])
    def test_complete_four_raw_groups(self):
        self.assertEqual(self.check(self.data()), {"source_delta": 14, "source_archives_added": 8,
                         "predecessor_receipts_added": 2, "current_executables": 18})
    def test_missing_duplicate_extra_and_wrong_paths_are_rejected(self):
        for key in ["source_delta", "source_archives_added", "predecessor_receipts_added", "current_executables"]:
            for mode in range(4):
                data = self.data()
                if mode == 0: data[key].pop()
                elif mode == 1: data[key].append(copy.deepcopy(data[key][0]))
                elif mode == 2: data[key].append({"path": "extra"})
                else: data[key][0]["path"] = "wrong"
                with self.assertRaises(ValueError): self.check(data)
    def test_raw_byte_hash_drift_is_rejected(self):
        with patch.object(M.BASE, "exact", return_value=False):
            with self.assertRaisesRegex(ValueError, "current_raw_pin_drift"):
                M.verify_current_manifest(self.data(), {"previous_checkpoint": {"path": M.PREVIOUS}})
    def test_native_full_import_registry_issuer_sql_publication_gate_promotion_denied(self):
        for key in M.FALSE_QUALIFICATIONS:
            data = self.data(); data["qualification"][key] = True
            with self.assertRaises(ValueError): self.check(data)
        for key, value in [("P09_gate", "PASS"), ("P10_new_implementation", True), ("product_complete", True),
                           ("remaining_coarse_groups_minimum", 5), ("remaining_coarse_groups_closed_by_slice", 1)]:
            data = self.data(); data[key] = value
            with self.assertRaises(ValueError): self.check(data)
        data = self.data(); data["qualification"]["actual_source_original_compiler_binding_verified"] = False
        with self.assertRaises(ValueError): self.check(data)
    def test_predecessor_identity_and_source_coverage_are_exact(self):
        for key, value in [("current_source_files_count", 1020), ("inherited_checkpoint", {"path": "wrong"})]:
            data = self.data(); data[key] = value
            with self.assertRaises(ValueError): self.check(data)
    def test_all_new_sources_exist_and_declared_phase_paths_are_correct(self):
        self.assertEqual(len(M.NEW_SOURCES), 12)
        for path in M.NEW_SOURCES:
            self.assertTrue((M.ROOT / path).is_file(), path)
            if path.startswith("implementation/p09/") and path.endswith(".md"):
                self.assertIn("P09-114_", path)
        self.assertEqual(M.NEW_SOURCES[8], "protocol/migrations/p09-stored-formula-compiler-v0-to-v1.md")
    def test_fixture_is_original_batch_body_with_only_import_rebinding(self):
        old = (M.ROOT / "crates/hwpx-package/tests/support/document_import_formula_batch_fixture.rs").read_text()
        new = (M.ROOT / M.NEW_SOURCES[3]).read_text()
        old = old.replace('#[path = "document_import_formula_output_fixture.rs"]',
                          '#[path = "../../../../../hwpx-package/tests/support/document_import_formula_output_fixture.rs"]')
        old = old.replace('#[path = "document_import_formula_evaluation_fixture.rs"]\npub mod source;',
                          'use super::super::formula_evaluation::fixture as source;')
        self.assertEqual(old, new)
    def test_physical_frozen_current_manifest_retains_all_remaining_groups(self):
        data = json.loads((M.ROOT / M.CURRENT).read_bytes())
        self.assertEqual(M.verify_current_manifest(data, {"previous_checkpoint": M.BASE.pin(M.PREVIOUS)})["source_delta"], 14)
        self.assertEqual(data["remaining_coarse_groups_minimum"], 6)
        self.assertEqual(data["remaining_coarse_groups_closed_by_slice"], 0)

if __name__ == "__main__":
    unittest.main()
