"""Source/pin contract tests, not native or real SQL acceptance."""
import copy
import importlib.util
import json
import unittest
from pathlib import Path
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location("p112_bytes", Path(__file__).parents[1] / "verify_formula_result_output_progress.py")
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)

class FormulaOutputProgressTests(unittest.TestCase):
    def data(self):
        groups = {"source_delta": M.PARENTS + M.NEW_SOURCES, "source_archives_added": M.ARCHIVES,
                  "predecessor_receipts_added": M.PREDECESSORS, "current_executables": M.EXECUTABLES}
        data = {key: [{"path": path, "bytes": 1, "sha256": "0" * 64} for path in paths] for key, paths in groups.items()}
        data.update({"inherited_checkpoint": {"path": M.PREVIOUS}, "current_source_files_count": 997,
                     "qualification": {key: False for key in M.FALSE_QUALIFICATIONS},
                     "P09_gate": "OPEN", "P10_new_implementation": False, "product_complete": False})
        data["qualification"]["original_computed_results_preserving_candidate_bound"] = True
        return data
    def check(self, data):
        with patch.object(M.BASE, "exact", return_value=True):
            return M.verify_current_manifest(data, {"previous_checkpoint": {"path": M.PREVIOUS}})
    def test_six_whole_actual_parent_inverses_retain_all_preexisting_source_bytes(self):
        sources = M.original_sources()
        self.assertEqual(len(sources), 980)
        for path in M.PARENTS:
            raw = (M.ROOT / path).read_bytes()
            archived = (M.ROOT / (M.ARCHIVE + path)).read_bytes()
            self.assertEqual(M.restored_parent(path, raw), archived)
            self.assertNotEqual(M.restored_parent(path, raw + b"\nUNDECLARED"), archived)
    def test_declared_parent_additions_are_exact_and_not_optional(self):
        for path in M.PARENTS:
            with self.assertRaises(ValueError):
                M.restored_parent(path, (M.ROOT / (M.ARCHIVE + path)).read_bytes())
        with self.assertRaises(ValueError):
            M.restored_parent("unknown", b"")
    def test_manifest_requires_all_twenty_three_delta_seventeen_archives_two_receipts_twenty_nine_executables(self):
        self.assertEqual(self.check(self.data()), {"source_delta": 23, "source_archives_added": 17, "predecessor_receipts_added": 2, "current_executables": 29})
    def test_missing_duplicate_extra_or_wrong_paths_never_satisfy_complete_inventory(self):
        for key in ["source_delta", "source_archives_added", "predecessor_receipts_added", "current_executables"]:
            for mode in range(4):
                data = self.data()
                if mode == 0: data[key].pop()
                elif mode == 1: data[key].append(copy.deepcopy(data[key][0]))
                elif mode == 2: data[key].append({"path": "extra"})
                else: data[key][0]["path"] = "wrong"
                with self.assertRaises(ValueError): self.check(data)
    def test_hash_drift_is_rejected_even_when_every_path_is_present(self):
        with patch.object(M.BASE, "exact", return_value=False):
            with self.assertRaisesRegex(ValueError, "current_raw_pin_drift"):
                M.verify_current_manifest(self.data(), {"previous_checkpoint": {"path": M.PREVIOUS}})
    def test_no_native_sql_issuer_atomic_execution_or_gate_claim_can_be_promoted(self):
        for key in M.FALSE_QUALIFICATIONS:
            data = self.data()
            data["qualification"][key] = True
            with self.assertRaises(ValueError): self.check(data)
        for key, value in [("P09_gate", "PASS"), ("P10_new_implementation", True), ("product_complete", True)]:
            data = self.data(); data[key] = value
            with self.assertRaises(ValueError): self.check(data)
    def test_every_new_source_is_real_and_uses_the_current_p09_phase(self):
        self.assertEqual(len(M.NEW_SOURCES), 17)
        for path in M.NEW_SOURCES:
            self.assertTrue((M.ROOT / path).is_file(), path)
            if path.endswith(".md"): self.assertIn("112", path)
    def test_frozen_current_live_manifest_matches_declarations_without_native_promotion(self):
        data = json.loads((M.ROOT / M.CURRENT).read_bytes())
        self.assertEqual(M.verify_current_manifest(data, {"previous_checkpoint": M.BASE.pin(M.PREVIOUS)})["source_delta"], 23)
        self.assertEqual(data["remaining_coarse_groups_minimum"], 6)
        self.assertEqual(data["remaining_coarse_groups_closed_by_slice"], 0)

if __name__ == "__main__":
    unittest.main()

