"""Scheduler unit only; 실제 resource guard는 원래 runner에서 그대로 수행한다."""
import importlib.util
import json
import unittest
from pathlib import Path

SPEC = importlib.util.spec_from_file_location(
    "p125", Path(__file__).parents[1] / "run_resumable_formula_batch.py"
)
P125 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(P125)


class Scheduler(unittest.TestCase):
    def check(self, count=0, elapsed=0, last_exit=0, pending=1, limit=25):
        return P125.may_start({"next_index": pending}, count, limit, elapsed, 120, last_exit)

    def test_start(self): self.assertTrue(self.check())
    def test_case_limit_stops(self): self.assertFalse(self.check(count=25))
    def test_time_limit_stops(self): self.assertFalse(self.check(elapsed=120))
    def test_failure_never_retries(self): self.assertFalse(self.check(last_exit=1))
    def test_deferred_never_retries(self): self.assertFalse(self.check(last_exit=2))
    def test_no_remaining_case(self): self.assertFalse(self.check(pending=None))
    def test_invalid_limit_rejected(self):
        with self.assertRaises(ValueError): self.check(limit=31)
    def test_bool_limit_rejected(self):
        with self.assertRaises(ValueError): self.check(limit=True)

    def test_actual_zero_after_exit_is_not_ram_sample(self):
        doc = json.loads((P125.R.ROOT / P125.R.RUN_DIR / "p124-case-021-attempt-001.json").read_bytes())
        observed = P125.resource_summary(doc)
        self.assertFalse(observed["test_ram_sampled"])
        self.assertIsNone(observed["max_observed_test_ram_mib"])

    def test_actual_positive_sample_retained(self):
        doc = json.loads((P125.R.ROOT / P125.R.RUN_DIR / "p124-case-019-attempt-001.json").read_bytes())
        observed = P125.resource_summary(doc)
        self.assertTrue(observed["test_ram_sampled"])
        self.assertEqual(observed["max_observed_test_ram_mib"], 20.76)


if __name__ == "__main__": unittest.main(verbosity=1)
