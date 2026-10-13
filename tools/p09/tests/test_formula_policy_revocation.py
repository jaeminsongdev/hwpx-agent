"""P134 evidence guard unit checks; do not execute any SQL/Hangul/approval UI."""
import copy
import importlib.util
import unittest
from pathlib import Path

SPEC = importlib.util.spec_from_file_location("p134_guard", Path(__file__).resolve().parents[1] / "verify_formula_policy_revocation.py")
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)


def tests():
    return {"terminal_summary": {"outcome": "ok", "passed": 2, "failed": 0, "ignored": 0, "measured": 0, "filtered": 228},
            "passed_test_names": ["one", "two"], "failed_test_names": []}


def resources():
    return {"logical_cpu_limit": 1, "affinity_mask": 1, "cargo_jobs": 1, "priority": "BelowNormal", "sample_seconds": 2,
            "cpu_stop_percent": 85, "cpu_stop_consecutive_samples": 3, "minimum_available_ram_mib": 4096,
            "maximum_root_working_set_mib": 2048, "elapsed_seconds": 1, "maximum_seconds": 60,
            "samples": [{"system_cpu_percent": 20, "available_ram_mib": 12000, "test_working_set_mib": 20}]}


class Guards(unittest.TestCase):
    def test_exact_selected_scope_accepts_only_its_declared_filter_count(self):
        M.validate_summary(tests(), {"one", "two"}, 228)

    def test_filtered_subset_cannot_be_promoted_to_full_regression(self):
        with self.assertRaisesRegex(ValueError, "revocation_runtime_coverage_incomplete"):
            M.validate_summary(tests(), {"one", "two"})

    def test_missing_or_duplicate_names_deny(self):
        for names in [["one"], ["one", "one"], ["one", "two", "three"]]:
            doc = tests()
            doc["passed_test_names"] = names
            with self.assertRaises(ValueError):
                M.validate_summary(doc, {"one", "two"}, 228)

    def test_ignored_measured_failed_or_wrong_filter_deny(self):
        for field in ("ignored", "measured", "failed", "filtered", "passed"):
            doc = tests()
            doc["terminal_summary"][field] += 1
            with self.assertRaises(ValueError):
                M.validate_summary(doc, {"one", "two"}, 228)

    def test_failed_names_are_never_accepted(self):
        doc = tests()
        doc["failed_test_names"] = ["private_failure"]
        with self.assertRaises(ValueError):
            M.validate_summary(doc, {"one", "two"}, 228)

    def test_normal_resource_policy_passes(self):
        M.resource(resources())

    def test_hot_start_denies(self):
        doc = resources()
        doc["samples"][0]["system_cpu_percent"] = 85
        with self.assertRaisesRegex(ValueError, "hot_revocation_start"):
            M.resource(doc)

    def test_three_consecutive_hot_samples_deny(self):
        doc = resources()
        hot = copy.deepcopy(doc["samples"][0])
        hot["system_cpu_percent"] = 100
        doc["samples"] += [copy.deepcopy(hot) for _ in range(3)]
        with self.assertRaises(ValueError):
            M.resource(doc)

    def test_low_ram_and_large_root_working_set_deny(self):
        for field, value in [("available_ram_mib", 4095), ("test_working_set_mib", 2049)]:
            doc = resources()
            doc["samples"][0][field] = value
            with self.assertRaises(ValueError):
                M.resource(doc)

    def test_resource_policy_and_timeout_cannot_be_weakened(self):
        for field, value in [("logical_cpu_limit", 2), ("cargo_jobs", 2), ("priority", "Normal"),
                             ("cpu_stop_percent", 100), ("minimum_available_ram_mib", 100), ("elapsed_seconds", 61)]:
            doc = resources()
            doc[field] = value
            with self.assertRaises(ValueError):
                M.resource(doc)

    def test_original_parent_modules_have_only_declared_additions(self):
        M.parent_edits()

    def test_current_full_inventory_keeps_existing_228_plus_new_6(self):
        self.assertEqual(len(M.expected_names("Stored")), 234)
        self.assertEqual(len(M.expected_names("Revocation")), 6)

    def test_current_source_freeze_has_all_781_declared_inputs(self):
        self.assertEqual(len(M.source_paths()), 781)


if __name__ == "__main__":
    unittest.main()
