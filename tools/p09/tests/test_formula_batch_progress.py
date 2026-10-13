"""Whole source/pin contracts; no native, real SQL or Gate qualification."""
import copy
import importlib.util
import json
import unittest
from pathlib import Path
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location("p113_bytes", Path(__file__).parents[1] / "verify_formula_batch_progress.py")
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)

class FormulaBatchProgressTests(unittest.TestCase):
    def data(self):
        groups = {"source_delta": [M.PARENT] + M.NEW_SOURCES, "source_archives_added": M.ARCHIVES,
                  "predecessor_receipts_added": M.PREDECESSORS, "current_executables": M.EXECUTABLES}
        data = {key: [{"path": path, "bytes": 1, "sha256": "0"*64} for path in paths] for key, paths in groups.items()}
        data.update({"inherited_checkpoint": {"path": M.PREVIOUS}, "current_source_files_count": 1009,
                     "qualification": {key: False for key in M.FALSE_QUALIFICATIONS},
                     "P09_gate": "OPEN", "P10_new_implementation": False, "product_complete": False})
        data["qualification"]["actual_source_position_value_rebinding_verified"] = True
        return data
    def check(self, data):
        with patch.object(M.BASE, "exact", return_value=True):
            return M.verify_current_manifest(data, {"previous_checkpoint": {"path": M.PREVIOUS}})
    def test_whole_actual_parent_inverse_retains_all_preexisting_source_bytes(self):
        sources = M.original_sources()
        self.assertEqual(len(sources), 997)
        raw = (M.ROOT / M.PARENT).read_bytes()
        archived = (M.ROOT / (M.ARCHIVE + M.PARENT)).read_bytes()
        self.assertEqual(M.restored_parent(raw), archived)
        self.assertNotEqual(M.restored_parent(raw+b"\nUNDECLARED"), archived)
    def test_declared_edit_is_exact_and_cannot_be_missing_duplicated_or_optional(self):
        archived = (M.ROOT / (M.ARCHIVE + M.PARENT)).read_bytes()
        with self.assertRaises(ValueError): M.restored_parent(archived)
        raw = (M.ROOT / M.PARENT).read_bytes()
        for _, new in M.EDITS:
            with self.assertRaises(ValueError): M.restored_parent(raw+new.encode())
    def test_all_inventory_groups_are_complete(self):
        self.assertEqual(self.check(self.data()), {"source_delta": 13, "source_archives_added": 16,
                         "predecessor_receipts_added": 2, "current_executables": 23})
    def test_missing_duplicate_extra_or_wrong_paths_are_rejected(self):
        for key in ["source_delta", "source_archives_added", "predecessor_receipts_added", "current_executables"]:
            for mode in range(4):
                data = self.data()
                if mode == 0: data[key].pop()
                elif mode == 1: data[key].append(copy.deepcopy(data[key][0]))
                elif mode == 2: data[key].append({"path": "extra"})
                else: data[key][0]["path"] = "wrong"
                with self.assertRaises(ValueError): self.check(data)
    def test_raw_hash_drift_is_rejected_even_when_every_path_is_present(self):
        with patch.object(M.BASE, "exact", return_value=False):
            with self.assertRaisesRegex(ValueError, "current_raw_pin_drift"):
                M.verify_current_manifest(self.data(), {"previous_checkpoint": {"path": M.PREVIOUS}})
    def test_any_native_sql_issuer_publication_or_gate_promotion_is_rejected(self):
        for key in M.FALSE_QUALIFICATIONS:
            data = self.data(); data["qualification"][key] = True
            with self.assertRaises(ValueError): self.check(data)
        for key, value in [("P09_gate", "PASS"), ("P10_new_implementation", True), ("product_complete", True)]:
            data = self.data(); data[key] = value
            with self.assertRaises(ValueError): self.check(data)
        data = self.data(); data["qualification"]["actual_source_position_value_rebinding_verified"] = False
        with self.assertRaises(ValueError): self.check(data)
    def test_current_coverage_and_predecessor_identity_are_exact(self):
        for key, value in [("current_source_files_count", 1008), ("inherited_checkpoint", {"path": "wrong"})]:
            data = self.data(); data[key] = value
            with self.assertRaises(ValueError): self.check(data)
    def test_every_new_source_exists_and_uses_the_declared_current_phase_path(self):
        self.assertEqual(len(M.NEW_SOURCES), 12)
        for path in M.NEW_SOURCES:
            self.assertTrue((M.ROOT / path).is_file(), path)
            if path.startswith("implementation/p09/") and path.endswith(".md"):
                self.assertIn("P09-113_", path)
            if path.startswith("protocol/migrations/"):
                self.assertEqual(path, "protocol/migrations/p09-formula-batch-value-binding-v0-to-v1.md")
    def test_actual_frozen_current_manifest_does_not_close_any_coarse_group(self):
        data = json.loads((M.ROOT / M.CURRENT).read_bytes())
        self.assertEqual(M.verify_current_manifest(data, {"previous_checkpoint": M.BASE.pin(M.PREVIOUS)})["source_delta"], 13)
        self.assertEqual(data["remaining_coarse_groups_minimum"], 6)
        self.assertEqual(data["remaining_coarse_groups_closed_by_slice"], 0)

if __name__ == "__main__":
    unittest.main()
