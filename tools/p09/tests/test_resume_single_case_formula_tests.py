"""실제 root receipt로 승인 guard를 확인; 복제 변형은 unit이며 runtime 증거가 아니다."""
import copy
import importlib.util
import json
import unittest
from pathlib import Path

SPEC = importlib.util.spec_from_file_location(
    "p124", Path(__file__).parents[1] / "resume_single_case_formula_tests.py"
)
P124 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(P124)


class ResumeGuards(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc = json.loads((P124.ROOT / P124.P123.ROOT_RUNS[0]).read_bytes())
        cls.name = P124.P123.ROOT_NAMES[0]
        cls.freeze = cls.doc["source_freeze"]

    def test_real_prior_single_case_positive(self):
        self.assertTrue(P124.accept_one(self.doc, self.name, self.freeze))

    def reject(self, mutate):
        doc = copy.deepcopy(self.doc)
        mutate(doc)
        with self.assertRaises(ValueError):
            P124.accept_one(doc, self.name, self.freeze)

    def test_no_terminal_rejected(self):
        self.reject(lambda d: d["tests"].update(terminal_summary=None))

    def test_filter_collision_receipt_rejected(self):
        self.reject(lambda d: d["tests"]["terminal_summary"].update(passed=2, filtered=226))

    def test_wrong_case_rejected(self):
        self.reject(lambda d: d["tests"].update(passed_test_names=["other_case"]))

    def test_executable_drift_rejected(self):
        self.reject(lambda d: d["executable_pin"].update(sha256="0" * 64))

    def test_source_drift_rejected(self):
        self.reject(lambda d: d.update(source_freeze=[]))

    def test_threshold_relaxation_rejected(self):
        self.reject(lambda d: d["plan"].update(minimum_available_ram_mib=0))

    def test_case_resume(self):
        status = P124.progress([self.name, "next"], [("p124-case-001-attempt-001.json", self.doc)], self.freeze)
        self.assertEqual((status["accepted"], status["remaining"], status["next_index"]), (1, 1, 2))

    def test_interrupted_not_accepted(self):
        doc = copy.deepcopy(self.doc)
        doc.update(state="NOT_ACCEPTED_STOP_OR_FAILURE", stop_reason="STOP_LOW_AVAILABLE_RAM")
        status = P124.progress([self.name], [("p124-case-001-attempt-001.json", doc)], self.freeze)
        self.assertEqual((status["accepted"], status["next_attempt"]), (0, 2))

    def test_duplicate_accepted_rejected(self):
        with self.assertRaises(ValueError):
            P124.progress([self.name], [("p124-case-001-attempt-001.json", self.doc),
                                      ("p124-case-001-attempt-002.json", self.doc)], self.freeze)

    def test_unknown_state_rejected(self):
        with self.assertRaises(ValueError):
            P124.progress([self.name], [("p124-case-001-attempt-001.json", {"state": "fake"})], self.freeze)

    def test_inventory_count_rejected(self):
        with self.assertRaises(ValueError):
            P124.inventory("one: test\n")

    def test_inventory_disjoint_scope_positive(self):
        names = [f"actual_import::case_{i:03d}" for i in range(200)]
        names += [f"full_document::case_{i:03d}" for i in range(20)]
        names += P124.P123.ROOT_NAMES
        self.assertEqual(len(P124.inventory("\n".join(n + ": test" for n in names))), 200)

    def test_inventory_substring_collision_rejected(self):
        names = [f"actual_import::case_{i:03d}" for i in range(200)]
        names[1] = names[0] + "_extra"
        names += [f"full_document::case_{i:03d}" for i in range(20)]
        names += P124.P123.ROOT_NAMES
        with self.assertRaises(ValueError):
            P124.inventory("\n".join(n + ": test" for n in names))


if __name__ == "__main__":
    unittest.main(verbosity=1)
