"""P133 strict-lint, exact-fixture and current runtime counterexamples."""
import copy
import importlib.util
import unittest
from pathlib import Path

SPEC = importlib.util.spec_from_file_location("p133", Path(__file__).resolve().parents[1] / "verify_optimized_workspace_lint.py")
V = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(V)


class OptimizedLintGuards(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc = V.R.read(V.RUN)
        cls.catalog = V.R.read(V.CAT_RUNS[2])

    def reject(self, mutation):
        doc = copy.deepcopy(self.doc)
        mutation(doc)
        with self.assertRaises((ValueError, KeyError, TypeError)):
            V.validate_lint(doc)

    def test_actual_full_lint_accepts(self):
        result = V.validate_lint(self.doc)
        self.assertEqual((result["workspace_packages"], result["workspace_targets"]), (32, 358))

    def test_current_catalog_accepts(self):
        self.assertGreater(V.validate_catalog(self.catalog, "Test")["observed_isolated_speedup"], 1)

    def test_declared_fixture_transition_is_exact(self):
        V.validate_fixture_transition((V.ROOT / V.ARCHIVES[V.PRE.OVERLAY]).read_text(encoding="utf-8"),
                                      (V.ROOT / V.INTERMEDIATE).read_text(encoding="utf-8"),
                                      (V.ROOT / V.PRE.OVERLAY).read_text(encoding="utf-8"))

    def test_initial_failures_and_defer_are_preserved(self):
        V.validate_failed_lint()

    def test_warning_rejects(self):
        self.reject(lambda d: d["diagnostics"].append({"level":"warning", "code":None, "spans":[]}))

    def test_artifact_target_omission_rejects(self):
        self.reject(lambda d: d.__setitem__("workspace_artifacts", [a for a in d["workspace_artifacts"]
                                                                 if a["name"] != "comment_style_section_protection"]))

    def test_unexpected_artifact_rejects(self):
        self.reject(lambda d: d["workspace_artifacts"][0].__setitem__("name", "unadmitted_target"))

    def test_source_omission_rejects(self):
        self.reject(lambda d: d["source_freeze"].pop())

    def test_runtime_promotion_rejects(self):
        self.reject(lambda d: d.__setitem__("test_or_app_executed", True))

    def test_more_cpu_rejects(self):
        self.reject(lambda d: d.__setitem__("logical_cpu_limit", 2))

    def test_low_ram_sample_rejects(self):
        self.reject(lambda d: d["samples"][0].__setitem__("available_ram_mib", 4095))

    def test_raw_log_payload_rejects(self):
        self.reject(lambda d: d["diagnostics"].append({"level":"note", "code":None, "spans":[], "rendered":"forbidden"}))

    def test_relaxed_lint_arguments_reject(self):
        self.reject(lambda d: d["cargo_arguments"].__setitem__(-2, "-A"))

    def test_source_hash_drift_rejects(self):
        self.reject(lambda d: d["source_freeze"][0].__setitem__("sha256", "0" * 64))

    def test_old_catalog_executable_rejects(self):
        doc = copy.deepcopy(self.catalog)
        doc["executable_pin"] = doc["protected_executables"][-1]
        with self.assertRaises(ValueError):
            V.validate_catalog(doc, "Test")

    def test_undeclared_fixture_change_rejects(self):
        with self.assertRaises(ValueError):
            V.validate_fixture_transition((V.ROOT / V.ARCHIVES[V.PRE.OVERLAY]).read_text(encoding="utf-8"),
                                          (V.ROOT / V.INTERMEDIATE).read_text(encoding="utf-8"),
                                          (V.ROOT / V.PRE.OVERLAY).read_text(encoding="utf-8") + "\n")


if __name__ == "__main__":
    unittest.main()
