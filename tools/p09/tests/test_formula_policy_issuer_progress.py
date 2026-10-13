"""Evidence guard regressions, NOT execution, native or production trust evidence."""
import copy
import importlib.util
import json
import unittest
from pathlib import Path

SPEC = importlib.util.spec_from_file_location("p119_bytes", Path(__file__).parents[1] / "verify_formula_policy_issuer_progress.py")
V = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(V)

class EvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.prior = V.inherited()
        cls.data = json.loads((V.ROOT / V.CURRENT).read_bytes())
    def test_whole_predecessor_audit_and_exact_parent_inverses(self):
        self.assertEqual(self.prior["unchanged_previous_source_files"], 1067)
        self.assertTrue(self.prior["previous_unmodified_audit_on_preimages_passed"])
        self.assertEqual(self.prior["old_executables_preserved"], 482)
    def test_exact_current_inventory(self):
        self.assertEqual(V.verify_current_manifest(self.data, self.prior), {
            "source_delta": 14, "source_archives_added": 8, "predecessor_receipts_added": 2, "current_executables": 15})
    def test_missing_duplicate_extra_or_changed_pin_is_rejected_in_every_group(self):
        for group in ["source_delta", "source_archives_added", "predecessor_receipts_added", "current_executables"]:
            for change in ["missing", "duplicate", "extra", "hash", "bytes"]:
                data = copy.deepcopy(self.data)
                if change == "missing": data[group].pop()
                elif change == "duplicate": data[group].append(copy.deepcopy(data[group][0]))
                elif change == "extra": data[group].append({"path": "not-in-scope", "bytes": 0, "sha256": "0" * 64})
                elif change == "hash": data[group][0]["sha256"] = "0" * 64
                else: data[group][0]["bytes"] += 1
                with self.subTest(group=group, change=change), self.assertRaises(ValueError):
                    V.verify_current_manifest(data, self.prior)
    def test_unsupported_qualifications_never_promote(self):
        for key in V.FALSE_QUALIFICATIONS:
            data = copy.deepcopy(self.data)
            data["qualification"][key] = True
            with self.subTest(key=key), self.assertRaises(ValueError):
                V.verify_current_manifest(data, self.prior)
    def test_product_gate_and_remaining_count_cannot_be_promoted(self):
        for key, value in [("P09_gate", "PASS"), ("P10_new_implementation", True), ("product_complete", True),
                           ("remaining_coarse_groups_minimum", 5), ("remaining_coarse_groups_closed_by_slice", 1),
                           ("conversation_minimum_30_conditions_not_exhaustive_or_decremented", False),
                           ("current_source_files_count", 1080)]:
            data = copy.deepcopy(self.data)
            data[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                V.verify_current_manifest(data, self.prior)
    def test_undeclared_parent_mutation_and_missing_edit_are_rejected(self):
        for path in V.PARENTS:
            archive = (V.ROOT / (V.ARCHIVE + path)).read_bytes()
            current = (V.ROOT / path).read_bytes()
            self.assertEqual(V.restored_parent(path, current), archive)
            self.assertNotEqual(V.restored_parent(path, current + b"undeclared change"), archive)
            with self.assertRaises(ValueError): V.restored_parent(path, archive)
    def test_runtime_source_and_executable_evidence_cannot_drift_or_expand(self):
        original = json.loads((V.ROOT / V.NEW_SOURCES[-1]).read_bytes())
        for case in range(10):
            data = copy.deepcopy(original)
            if case == 0: data["state"] = "IN_PROGRESS"
            elif case == 1: data["source_freeze"].pop()
            elif case == 2: data["source_freeze"][0]["sha256"] = "0" * 64
            elif case == 3: data["runtime"]["passed"] = 315
            elif case == 4: data["runtime"]["filtered"] = 1
            elif case == 5: data["runtime"]["suites"]["form_stored_provider"] = 221
            elif case == 6: data["test_inventory"]["test_executables"].pop()
            elif case == 7: data["test_inventory"]["test_executables"][0]["sha256"] = "0" * 64
            elif case == 8: data["source_freeze_verified_in_run"]["code_freeze_9_exact"] = False
            else: data["runtime"]["full_workspace_run"] = True
            with self.subTest(case=case), self.assertRaises(ValueError):
                V.verify_regression(data, self.data)

if __name__ == "__main__":
    unittest.main()
