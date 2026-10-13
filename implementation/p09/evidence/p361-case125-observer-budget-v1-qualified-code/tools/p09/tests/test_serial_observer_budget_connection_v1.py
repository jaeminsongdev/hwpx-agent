"""Connection contracts; no real Windows/PDH/product calls."""
from pathlib import Path
import sys
import unittest
from types import SimpleNamespace as NS

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import serial_observer_budget_connection_v1 as c
import accept_case112_current_epoch as a
from test_serial_cpu_attribution_budget_v1 import Fake


class Original:
    def __init__(self):
        self.processors=16;self.last=(100,200,100);self.cpu=20.;self.error=None
    def sample(self):
        if self.error:raise ValueError(self.error)
        self.last=tuple(v+100 for v in self.last)
        return dict(system_cpu_percent=self.cpu,available_ram_percent=30.,commit_used_percent=40.)


class ConnectionContracts(unittest.TestCase):
    def make(self, cost=0):
        raw=(Path(__file__).resolve().parents[3]/c.budget.ORIGINAL_PIN["path"]).read_bytes()
        cls, proof=c.budget.make_probe(raw)
        api=Fake(collect_cost=cost)
        class Probe(cls):
            def __init__(self, processors):
                super().__init__(processors,api=api,clock=lambda:api.now)
        view=c.view(Probe,proof);objects=[]
        window=view.windows_type(Original,objects)()
        self.addCleanup(lambda:view.close(objects))
        return view,objects,window,api
    def test_one_original_observer_and_bound_budget_probe(self):
        view,objects,window,api=self.make()
        row=window.sample();summary=view.summary(objects)
        self.assertEqual(len(objects),1)
        self.assertTrue(summary["early_budget_probe_connection"]["instance_binding_observed"])
        self.assertEqual(row["system_cpu_percent"],20.)
        self.assertEqual(a.c.decision(row,0),(0,None))
    def test_original_resource_error_before_any_probe_sample(self):
        view,objects,window,api=self.make()
        before=api.collects;window.error="CPU_SAMPLE_INTERVAL_MISSING"
        with self.assertRaisesRegex(ValueError,"CPU_SAMPLE_INTERVAL_MISSING"):window.sample()
        self.assertEqual(api.collects,before)
    def test_warning_forces_fresh_but_preserves_K32_CPU(self):
        view,objects,window,api=self.make()
        window.sample();before=api.collects;window.cpu=100.
        row=window.sample()
        self.assertEqual(api.collects,before+1)
        self.assertEqual(a.c.decision(row,3),(4,"STOP_SUSTAINED_SYSTEM_CPU"))
        self.assertFalse(row["serial_cpu_attribution"]["identical_to_original_K32_interval"])
    def test_cold_interval_does_not_query_again_or_invent_zero(self):
        view,objects,window,api=self.make()
        window.sample();before=api.collects;row=window.sample()
        self.assertEqual(api.collects,before)
        self.assertIsNone(row["serial_cpu_attribution"]["values"])
    def test_slow_collect_closes_without_formatted_values(self):
        view,objects,window,api=self.make(.086)
        before=api.reads;row=window.sample()
        self.assertEqual(api.reads,before)
        self.assertFalse(row["serial_cpu_attribution"]["available"])
        self.assertTrue(view.close(objects))
    def test_failed_close_preserved(self):
        view,objects,window,api=self.make(.086)
        api.close_code=123;window.sample()
        self.assertFalse(view.close(objects))
        self.assertFalse(view.summary(objects)["probes"][0]["cleanup_confirmed"])
        api.close_code=0;self.assertTrue(view.close(objects))
    def test_invalid_factory_type_refused(self):
        with self.assertRaisesRegex(ValueError,"EXACT_BUDGET_PROBE_TYPE"):c.view(object,{})
    def test_entry_changes_only_local_dependency_without_bytecode_mutation(self):
        raw=(Path(__file__).resolve().parents[3]/c.budget.ORIGINAL_PIN["path"]).read_bytes()
        env=dict(attribution=c.original,other=object())
        exec("def run_owned(run): return run",env)
        api=NS(run_owned=env["run_owned"]);before=api.run_owned.__code__
        proof=c.bind_entry(api,raw)
        self.assertIs(api.run_owned.__code__,before)
        self.assertEqual(proof["local_dependency_changes"],1)
        self.assertIsNot(env["attribution"],c.original)
    def test_non_original_entry_dependency_refused(self):
        env=dict(attribution=object())
        exec("def run_owned(run): return run",env)
        with self.assertRaisesRegex(ValueError,"ORIGINAL_LOCAL_ATTRIBUTION_DEPENDENCY"):
            c.bind_entry(NS(run_owned=env["run_owned"]),b"not needed")


if __name__=="__main__":unittest.main()
