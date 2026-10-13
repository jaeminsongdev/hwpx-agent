"""Whole-source ancestry, field-policy data boundary and unsupported authority promotion checks."""
import copy
import importlib.util
import json
import unittest
from pathlib import Path
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location("p116_bytes", Path(__file__).parents[1] / "verify_formula_policy_progress.py")
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)

class FormulaPolicyProgressTests(unittest.TestCase):
    def data(self):
        groups = {"source_delta": M.PARENTS + M.NEW_SOURCES, "source_archives_added": M.ARCHIVES,
                  "predecessor_receipts_added": M.PREDECESSORS, "current_executables": M.EXECUTABLES}
        data = {key: [{"path": path, "bytes": 1, "sha256": "0"*64} for path in paths] for key, paths in groups.items()}
        data.update({"inherited_checkpoint": {"path": M.PREVIOUS}, "current_source_files_count": 1047,
                     "qualification": {key: False for key in M.FALSE_QUALIFICATIONS},
                     "P09_gate": "OPEN", "P10_new_implementation": False, "product_complete": False,
                     "remaining_coarse_groups_minimum": 6, "remaining_coarse_groups_closed_by_slice": 0})
        data["qualification"]["actual_source_formula_policy_data_binding_verified"] = True
        data["qualification"]["original_product_formula_policy_data_gating_verified"] = True
        return data

    def check(self, data):
        with patch.object(M.BASE, "exact", return_value=True):
            return M.verify_current_manifest(data, {"previous_checkpoint": {"path": M.PREVIOUS}})

    def test_four_parent_preimages_exact_inverse_no_unrelated_rewrites(self):
        self.assertEqual(len(M.original_sources()), 1034)
        for path in M.PARENTS:
            raw = (M.ROOT / path).read_bytes()
            archived = (M.ROOT / (M.ARCHIVE + path)).read_bytes()
            self.assertEqual(M.restored_parent(path, raw), archived)
            self.assertNotEqual(M.restored_parent(path, raw+b"\nUNDECLARED"), archived)
            with self.assertRaises(ValueError):
                M.restored_parent(path, archived)
            for edit in M.EDITS[path]:
                with self.assertRaises(ValueError):
                    M.restored_parent(path, raw+edit)

    def test_all_exact_raw_inventory_groups_are_required(self):
        expected = {"source_delta": 17, "source_archives_added": len(M.ARCHIVES),
                    "predecessor_receipts_added": 2, "current_executables": len(M.EXECUTABLES)}
        self.assertEqual(self.check(self.data()), expected)

    def test_missing_duplicate_extra_or_substituted_inventory_paths_rejected(self):
        for key in ["source_delta", "source_archives_added", "predecessor_receipts_added", "current_executables"]:
            for mode in range(4):
                data = self.data()
                if mode == 0: data[key].pop()
                elif mode == 1: data[key].append(copy.deepcopy(data[key][0]))
                elif mode == 2: data[key].append({"path": "extra"})
                else: data[key][0]["path"] = "wrong"
                with self.assertRaises(ValueError):
                    self.check(data)

    def test_actual_raw_hash_drift_rejected(self):
        with patch.object(M.BASE, "exact", return_value=False):
            with self.assertRaisesRegex(ValueError, "current_raw_pin_drift"):
                M.verify_current_manifest(self.data(), {"previous_checkpoint": {"path": M.PREVIOUS}})

    def test_issuer_sql_native_transport_execution_and_gate_not_promoted(self):
        for key in M.FALSE_QUALIFICATIONS:
            data = self.data()
            data["qualification"][key] = True
            with self.assertRaises(ValueError):
                self.check(data)
        for key, value in [("P09_gate", "PASS"), ("P10_new_implementation", True), ("product_complete", True),
                           ("remaining_coarse_groups_minimum", 5), ("remaining_coarse_groups_closed_by_slice", 1)]:
            data = self.data()
            data[key] = value
            with self.assertRaises(ValueError):
                self.check(data)
        for key in ["actual_source_formula_policy_data_binding_verified", "original_product_formula_policy_data_gating_verified"]:
            data = self.data()
            data["qualification"][key] = False
            with self.assertRaises(ValueError):
                self.check(data)

    def test_source_coverage_and_exact_predecessor_are_required(self):
        for key, value in [("current_source_files_count", 1046), ("inherited_checkpoint", {"path": "wrong"})]:
            data = self.data()
            data[key] = value
            with self.assertRaises(ValueError):
                self.check(data)

    def test_every_new_source_is_current_owned_scope_and_exists(self):
        self.assertEqual(len(M.NEW_SOURCES), 13)
        self.assertEqual(len(set(M.NEW_SOURCES)), 13)
        for path in M.NEW_SOURCES:
            self.assertTrue((M.ROOT / path).is_file(), path)
        self.assertEqual(M.NEW_SOURCES[9], "protocol/migrations/p09-source-formula-policy-v0-to-v1.md")

    def test_frozen_physical_current_data_manifest_does_not_reduce_residual_groups(self):
        data = json.loads((M.ROOT / M.CURRENT).read_bytes())
        result = M.verify_current_manifest(data, {"previous_checkpoint": M.BASE.pin(M.PREVIOUS)})
        self.assertEqual(result["source_delta"], 17)
        self.assertEqual(data["remaining_coarse_groups_minimum"], 6)
        self.assertEqual(data["remaining_coarse_groups_closed_by_slice"], 0)

if __name__ == "__main__":
    unittest.main()
