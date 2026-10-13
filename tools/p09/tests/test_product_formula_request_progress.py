"""Exact four-parent source ancestry, bounded inventories and unsupported authority rejection."""
import copy
import importlib.util
import json
import unittest
from pathlib import Path
from unittest.mock import patch
SPEC = importlib.util.spec_from_file_location("p115_bytes", Path(__file__).parents[1] / "verify_product_formula_request_progress.py")
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)

class ProductFormulaRequestProgressTests(unittest.TestCase):
    def data(self):
        groups = {"source_delta": M.PARENTS + M.NEW_SOURCES, "source_archives_added": M.ARCHIVES,
                  "predecessor_receipts_added": M.PREDECESSORS, "current_executables": M.EXECUTABLES}
        data = {key: [{"path": path, "bytes": 1, "sha256": "0"*64} for path in paths] for key, paths in groups.items()}
        data.update({"inherited_checkpoint": {"path": M.PREVIOUS}, "current_source_files_count": 1034,
                     "qualification": {key: False for key in M.FALSE_QUALIFICATIONS},
                     "P09_gate": "OPEN", "P10_new_implementation": False, "product_complete": False,
                     "remaining_coarse_groups_minimum": 6, "remaining_coarse_groups_closed_by_slice": 0})
        data["qualification"]["actual_strict_product_request_dispatch_verified"] = True
        data["qualification"]["exact_original_protected_no_change_verified"] = True
        return data
    def check(self, data):
        with patch.object(M.BASE, "exact", return_value=True):
            return M.verify_current_manifest(data, {"previous_checkpoint": {"path": M.PREVIOUS}})
    def test_all_four_parent_preimages_and_exact_inverse_preserve_original_bytes(self):
        self.assertEqual(len(M.original_sources()), 1021)
        for path in M.PARENTS:
            raw = (M.ROOT / path).read_bytes()
            archived = (M.ROOT / (M.ARCHIVE + path)).read_bytes()
            self.assertEqual(M.restored_parent(path, raw), archived)
            self.assertNotEqual(M.restored_parent(path, raw+b"\nUNDECLARED"), archived)
            with self.assertRaises(ValueError): M.restored_parent(path, archived)
            with self.assertRaises(ValueError): M.restored_parent(path, raw+M.EDITS[path][1])
    def test_all_four_raw_inventory_groups_are_complete(self):
        self.assertEqual(self.check(self.data()), {"source_delta": 17, "source_archives_added": 20,
                         "predecessor_receipts_added": 2, "current_executables": 21})
    def test_missing_duplicate_extra_or_wrong_paths_are_rejected(self):
        for key in ["source_delta", "source_archives_added", "predecessor_receipts_added", "current_executables"]:
            for mode in range(4):
                data = self.data()
                if mode == 0: data[key].pop()
                elif mode == 1: data[key].append(copy.deepcopy(data[key][0]))
                elif mode == 2: data[key].append({"path": "extra"})
                else: data[key][0]["path"] = "wrong"
                with self.assertRaises(ValueError): self.check(data)
    def test_actual_byte_hash_drift_is_rejected(self):
        with patch.object(M.BASE, "exact", return_value=False):
            with self.assertRaisesRegex(ValueError, "current_raw_pin_drift"):
                M.verify_current_manifest(self.data(), {"previous_checkpoint": {"path": M.PREVIOUS}})
    def test_native_transport_execution_registry_issuer_sql_publication_gate_promotion_denied(self):
        for key in M.FALSE_QUALIFICATIONS:
            data = self.data(); data["qualification"][key] = True
            with self.assertRaises(ValueError): self.check(data)
        for key, value in [("P09_gate", "PASS"), ("P10_new_implementation", True), ("product_complete", True),
                           ("remaining_coarse_groups_minimum", 5), ("remaining_coarse_groups_closed_by_slice", 1)]:
            data = self.data(); data[key] = value
            with self.assertRaises(ValueError): self.check(data)
        for key in ["actual_strict_product_request_dispatch_verified", "exact_original_protected_no_change_verified"]:
            data = self.data(); data["qualification"][key] = False
            with self.assertRaises(ValueError): self.check(data)
    def test_predecessor_and_source_coverage_are_exact(self):
        for key, value in [("current_source_files_count", 1033), ("inherited_checkpoint", {"path": "wrong"})]:
            data = self.data(); data[key] = value
            with self.assertRaises(ValueError): self.check(data)
    def test_every_new_source_exists_in_its_declared_current_phase(self):
        self.assertEqual(len(M.NEW_SOURCES), 13)
        for path in M.NEW_SOURCES:
            self.assertTrue((M.ROOT / path).is_file(), path)
            if path.startswith("implementation/p09/") and path.endswith(".md"):
                self.assertIn("P09-115_", path)
        self.assertEqual(M.NEW_SOURCES[9], "protocol/migrations/p09-product-formula-request-v1-to-v2.md")
    def test_frozen_physical_current_manifest_does_not_reduce_remaining_groups(self):
        data = json.loads((M.ROOT / M.CURRENT).read_bytes())
        self.assertEqual(M.verify_current_manifest(data, {"previous_checkpoint": M.BASE.pin(M.PREVIOUS)})["source_delta"], 17)
        self.assertEqual(data["remaining_coarse_groups_minimum"], 6)
        self.assertEqual(data["remaining_coarse_groups_closed_by_slice"], 0)

if __name__ == "__main__":
    unittest.main()
