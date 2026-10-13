"""P129 signed-result and current-runtime counterexamples, not native qualification."""
import copy
import importlib.util
import unittest
from pathlib import Path

SPEC = importlib.util.spec_from_file_location("p129_audit", Path(__file__).resolve().parents[1] / "verify_current_stored_regression.py")
V = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(V)
R = V.R


class CurrentSignedGuardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original = R.read("implementation/p09/evidence/p09-120-signed-original-corpus.original-corpus.v1.json")["result"]
        cls.tests = [R.read(R.RUN + f"p124-case-{i:03d}-attempt-001.json")["tests"] for i in range(49, 53)]
        cls.changed = cls.tests[2]["changed_corpus_result"]

    def reject(self, mutation):
        tests = copy.deepcopy(self.tests)
        mutation(tests)
        with self.assertRaises((ValueError, KeyError, TypeError)):
            V.validate_signed_markers(tests, self.original, self.changed)

    def test_historical_exact_marker_fixture_accepts(self):
        V.validate_signed_markers(self.tests, self.original, self.changed)

    def test_changed_digest_substitution_rejects(self):
        self.reject(lambda t: t[2]["changed_corpus_result"]["rows"][0].__setitem__("candidate_sha256", "0" * 64))

    def test_missing_changed_row_rejects(self):
        self.reject(lambda t: t[2]["changed_corpus_result"]["rows"].pop())

    def test_original_identity_substitution_rejects(self):
        self.reject(lambda t: t[0]["corpus_result"]["originals"][0].__setitem__("source_sha256", "0" * 64))

    def test_outside_leaf_guard_missing_rejects(self):
        self.reject(lambda t: t[1].__setitem__("outside_leaf_counterexamples_pass", False))

    def test_protection_guard_missing_rejects(self):
        self.reject(lambda t: t[3].__setitem__("changed_protection_pass", False))

    def test_duplicate_inventory_rejects(self):
        names = R.read(R.LIST)["inventory"]
        names[0] = names[1]
        with self.assertRaises(ValueError):
            R.inventory(names)

    def test_missing_inventory_rejects(self):
        with self.assertRaises(ValueError):
            R.inventory(R.read(R.LIST)["inventory"][:-1])

    def test_actual_current_marker_accepts(self):
        names, freeze = R.preparation()
        V.validate_marker(R.read(V.MARKERS[0]), names[76], freeze)

    def test_actual_wrong_scope_attempt_rejects(self):
        names, freeze = R.preparation()
        with self.assertRaisesRegex(ValueError, "marker_case_identity_drift"):
            V.validate_marker(R.read(V.UNACCEPTED_MARKERS[0]), names[76], freeze)

    def test_current_marker_schema_substitution_rejects(self):
        names, freeze = R.preparation()
        doc = R.read(V.MARKERS[0])
        doc["schema_version"] = "hwpx-agent.p09-current-form-regression/v1"
        with self.assertRaises(ValueError):
            V.validate_marker(doc, names[76], freeze)


if __name__ == "__main__":
    unittest.main()
