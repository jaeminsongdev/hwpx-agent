"""Synthetic early-cost contracts; no real PDH/native/product work."""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import serial_cpu_attribution_budget_v1 as p


class Fake:
    def __init__(self, collect_cost=0, value_cost=0):
        self.now = 0.
        self.collect_cost = collect_cost
        self.value_cost = value_cost
        self.collects = 0
        self.reads = 0
        self.close_code = 0
        self.closed = 0
    def open(self): return 0, 1
    def add(self, query, path):
        return 0, next(n for n, v in p.original.PATHS.items() if v == path)
    def collect(self, query):
        self.collects += 1
        if self.collects > 1: self.now += self.collect_cost
        return 0
    def value(self, name, is_pid):
        self.reads += 1
        if self.collects > 1: self.now += self.value_cost
        value = 4 if name == "System_pid" else 5408 if name == "MsMpEng_pid" else 800. if name == "MsMpEng_cpu" else 0.
        return 0, 1, value
    def close(self, query):
        self.closed += 1
        return self.close_code


class BudgetContracts(unittest.TestCase):
    def make(self, **kw):
        # 로컬 단위 fixture만 읽음; 실제 qualification은 원 Guard/Reader로 별도.
        raw = (Path(__file__).resolve().parents[3] / p.ORIGINAL_PIN["path"]).read_bytes()
        cls, proof = p.make_probe(raw)
        api = Fake(**kw)
        probe = cls(16, api=api, clock=lambda: api.now)
        self.addCleanup(probe.close)
        return probe, api, proof
    def test_exact_ast_and_same_budgets(self):
        probe, api, proof = self.make()
        self.assertTrue(proof["original_sample_AST_restored_exactly"])
        self.assertEqual(proof["added_cost_sites"], 4)
        self.assertEqual(proof["original_maximum_sample_seconds"], .05)
        self.assertEqual(proof["original_maximum_total_seconds"], 2.)
    def test_normal_all_seven_reads_and_PID_binding_retained(self):
        probe, api, _ = self.make()
        before = api.reads
        row = probe.sample()
        self.assertTrue(row["available"])
        self.assertEqual(api.reads - before, 7)
        self.assertEqual(row["values"]["MsMpEng"]["machine_cpu_percent"], 50)
        self.assertFalse(row["identical_to_original_K32_interval"])
    def test_slow_collect_stops_before_any_formatted_read(self):
        probe, api, _ = self.make(collect_cost=.086)
        before = api.reads
        row = probe.sample()
        self.assertEqual(api.reads, before)
        self.assertIsNone(row["values"])
        self.assertFalse(row["available"])
        self.assertEqual(probe.early_budget_stops, 1)
        self.assertTrue(probe.cleanup)
        self.assertFalse(row["OS_call_hard_preemption_guaranteed"])
    def test_slow_read_stops_remaining_reads(self):
        probe, api, _ = self.make(value_cost=.06)
        before = api.reads
        row = probe.sample()
        self.assertEqual(api.reads - before, 1)
        self.assertIsNone(row["values"])
    def test_total_budget_stops_before_reads(self):
        probe, api, _ = self.make(collect_cost=.02)
        probe.total_latency = 1.99
        before = api.reads
        self.assertIsNone(probe.sample()["values"])
        self.assertEqual(api.reads, before)
    def test_stopped_probe_never_resumes_collect_or_reads(self):
        probe, api, _ = self.make(collect_cost=.086)
        probe.sample()
        counts = (api.collects, api.reads)
        self.assertEqual(probe.sample()["reason"], "MEASUREMENT_COST_BUDGET_EXCEEDED")
        self.assertEqual((api.collects, api.reads), counts)
    def test_failed_close_not_reported_clean_and_final_retry_retained(self):
        probe, api, _ = self.make(collect_cost=.086)
        api.close_code = 123
        probe.sample()
        self.assertFalse(probe.cleanup)
        self.assertIsNotNone(probe.query)
        api.close_code = 0
        self.assertTrue(probe.close())
    def test_original_invalid_source_refused(self):
        with self.assertRaisesRegex(ValueError, "EXACT_ORIGINAL_BYTES"):
            p.make_probe(b"not an original sample")
    def test_same_slow_collect_old_reads_seven_new_reads_zero(self):
        old_api = Fake(collect_cost=.086)
        old = p.original.Probe(16, api=old_api, clock=lambda: old_api.now)
        self.addCleanup(old.close)
        before = old_api.reads
        self.assertIsNone(old.sample()["values"])
        self.assertEqual(old_api.reads - before, 7)
        new, api, _ = self.make(collect_cost=.086)
        before = api.reads
        self.assertIsNone(new.sample()["values"])
        self.assertEqual(api.reads - before, 0)
    def test_owner_error_still_precedes_all_native_work(self):
        probe, api, _ = self.make()
        probe.owner = ("not the original owner", 99)
        before = (api.collects, api.reads)
        with self.assertRaisesRegex(ValueError, "SAME_ORIGINAL_OBSERVER_OWNER"):
            probe.sample()
        self.assertEqual((api.collects, api.reads), before)
    def test_slow_last_read_keeps_original_final_budget_check(self):
        probe, api, _ = self.make()
        old_value = api.value
        def value(name, is_pid):
            result = old_value(name, is_pid)
            if name == "interrupt_cpu": api.now += .06
            return result
        api.value = value
        row = probe.sample()
        self.assertIsNone(row["values"])
        self.assertEqual(probe.early_budget_stops, 0)
        self.assertEqual(probe.disabled_reason, "MEASUREMENT_COST_BUDGET_EXCEEDED")
        self.assertTrue(probe.cleanup)


if __name__ == "__main__":
    unittest.main()
