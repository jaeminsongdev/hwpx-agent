"""P135 case admission counterexamples; guard units are not extra product executions."""
import copy
import importlib.util
import unittest
from pathlib import Path

SPEC = importlib.util.spec_from_file_location("p135", Path(__file__).resolve().parents[1] / "run_final_stored_batch.py")
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)
VSPEC = importlib.util.spec_from_file_location("p135_verifier", Path(__file__).resolve().parents[1] / "verify_final_stored_regression.py")
V = importlib.util.module_from_spec(VSPEC)
VSPEC.loader.exec_module(V)


class Guards(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.names, cls.freeze = M.preparation()
        cls.doc = M.R.read(M.R.RUN + "p135-case-001-attempt-001.json")
        cls.name = cls.names[0]

    def reject(self, mutation):
        doc = copy.deepcopy(self.doc)
        mutation(doc)
        with self.assertRaises((ValueError, KeyError, TypeError)):
            M.accept_case(doc, self.name, self.freeze)

    def test_actual_exact_final_case_accepts(self):
        M.accept_case(self.doc, self.name, self.freeze)

    def test_reordered_freeze_is_still_the_same_exact_input_set(self):
        doc = copy.deepcopy(self.doc)
        doc["source_freeze"].reverse()
        M.accept_case(doc, self.name, self.freeze)

    def test_wrong_executable_or_case_denies(self):
        self.reject(lambda d: d["executable_pin"].__setitem__("sha256", "0"*64))
        self.reject(lambda d: d.__setitem__("test_name", "different_case"))

    def test_inexact_filter_or_parallel_worker_denies(self):
        self.reject(lambda d: d["arguments"].remove("--exact"))
        self.reject(lambda d: d.__setitem__("test_threads", 2))

    def test_duplicate_or_changed_input_denies(self):
        self.reject(lambda d: d["source_freeze"].__setitem__(0, d["source_freeze"][1]))
        self.reject(lambda d: d["source_freeze"][0].__setitem__("sha256", "0"*64))

    def test_false_preservation_denies(self):
        self.reject(lambda d: d.__setitem__("source_freeze_exact_after", False))
        self.reject(lambda d: d.__setitem__("protected_executables_exact_after", False))

    def test_gate_sql_or_native_scope_promotion_denies(self):
        for key, value in [("P09_gate", "PASS"), ("product_complete", True), ("actual_sql_executed", True), ("native_application_executed", True)]:
            self.reject(lambda d, k=key, v=value: d.__setitem__(k, v))

    def test_ignored_failed_measured_or_wrong_filtered_count_denies(self):
        for key in ("ignored", "failed", "measured", "filtered", "passed"):
            self.reject(lambda d, k=key: d["tests"]["terminal_summary"].__setitem__(k, d["tests"]["terminal_summary"][k]+1))

    def test_extra_or_duplicate_passed_name_denies(self):
        self.reject(lambda d: d["tests"]["passed_test_names"].append(self.name))

    def test_resource_policy_cannot_be_relaxed(self):
        for key, value in [("logical_cpu_limit", 2), ("affinity_mask", 2), ("priority", "Normal"), ("cpu_stop_percent", 100), ("minimum_available_ram_mib", 1)]:
            self.reject(lambda d, k=key, v=value: d.__setitem__(k, v))

    def test_low_ram_and_hot_start_deny(self):
        self.reject(lambda d: d["samples"][0].__setitem__("available_ram_mib", 4095))
        self.reject(lambda d: d["samples"][0].__setitem__("system_cpu_percent", 85))

    def test_batch_budget_and_case_limit_are_real_start_boundaries(self):
        self.assertTrue(M.may_start(0, 25, 0, 180, 0))
        self.assertFalse(M.may_start(25, 25, 0, 180, 0))
        self.assertFalse(M.may_start(0, 25, 180, 180, 0))
        self.assertFalse(M.may_start(0, 25, 0, 180, 2))
        for limit, budget in [(0, 180), (31, 180), (25, 0), (25, 301)]:
            with self.assertRaises(ValueError):
                M.may_start(0, limit, 0, budget, 0)

    def test_retry_uses_a_new_attempt_instead_of_overwriting(self):
        stops = [(3, 1, "old"), (3, 2, "old2"), (4, 5, "other")]
        self.assertEqual(M.next_attempt(3, stops), 3)
        self.assertEqual(M.next_attempt(1, stops), 1)

    def test_signed_boolean_markers_need_literal_true(self):
        for name, field in V.MARKERS.items():
            if field.endswith("corpus_result"):
                continue
            V.validate_marker_result(name, {field: True}, {}, {})
            for value in (False, 1, "true", None):
                with self.assertRaises(ValueError):
                    V.validate_marker_result(name, {field: value}, {}, {})

    def test_signed_corpus_payload_cannot_change_counts_or_leaf_bindings(self):
        original = M.R.read("implementation/p09/evidence/p09-120-signed-original-corpus.original-corpus.v1.json")["result"]
        changed = M.R.read(M.R.RUN + "p124-case-051-attempt-001.json")["tests"]["changed_corpus_result"]
        for name, field in V.MARKERS.items():
            if not field.endswith("corpus_result"):
                continue
            expected = original if field == "corpus_result" else changed
            V.validate_marker_result(name, {field: expected}, original, changed)
            with self.assertRaises(ValueError):
                V.validate_marker_result(name, {field: {}}, original, changed)
            altered = copy.deepcopy(expected)
            altered["unbound_extra_leaf"] = True
            with self.assertRaises(ValueError):
                V.validate_marker_result(name, {field: altered}, original, changed)

    def test_read_only_resource_pairs_cannot_promote_scope_or_relax_inputs(self):
        measured = M.R.read(V.MEASUREMENT)
        self.assertEqual(V.validate_measurement(measured), 3)
        for key, value in [("pressure_cause", "TEST_PROCESS"), ("P09_gate", "PASS"), ("stored_test_started", True),
                           ("system_settings_changed", True), ("existing_runner_or_thresholds_modified", True)]:
            doc = copy.deepcopy(measured)
            doc[key] = value
            with self.assertRaises(ValueError):
                V.validate_measurement(doc)
        for key, value in [("conservative_inputs", {"system_cpu_percent": 0, "available_ram_mib": 100000}),
                           ("resource_decision", "STOP_SUSTAINED_SYSTEM_CPU"), ("native_cpu_percent", float("nan")), ("index", True)]:
            doc = copy.deepcopy(measured)
            doc["samples"][0][key] = value
            with self.assertRaises(ValueError):
                V.validate_measurement(doc)


if __name__ == "__main__":
    unittest.main()
