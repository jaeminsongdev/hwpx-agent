import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
sys.path.insert(0,str(Path(__file__).resolve().parent))
import native_process_cpu_attribution_v4 as m
from test_native_process_cpu_attribution_v3 import API,Clock

class Tests(unittest.TestCase):
    def probe(self,api=None):
        api=API() if api is None else api
        return m.Probe(16,api=api,clock=Clock(),identity=lambda:(1,1)),api
    def test_warning_has_no_additional_query_no_baseline_or_zero_values(self):
        p,api=self.probe();previous=p.previous;queries=p.queries
        for cpu in (75.,93.,100.):
            row=p.sample(dict(system_cpu_percent=cpu))
            self.assertFalse(row["available"]);self.assertIsNone(row["values"])
            self.assertEqual(row["reason"],m.SUPPRESSED)
            self.assertFalse(row["optional_native_query_attempted"])
        self.assertEqual(api.calls,1);self.assertEqual(p.queries,queries)
        self.assertIs(p.previous,previous);self.assertEqual(p.samples,0)
        self.assertEqual(p.warning_attribution_suppressions,3);p.close()
    def test_low_load_uses_original_sample_and_original_K32_value(self):
        p,api=self.probe();row=p.sample(dict(system_cpu_percent=60.))
        self.assertTrue(row["available"]);self.assertEqual(row["values"]["total_cpu"],60.)
        self.assertEqual(api.calls,2);self.assertEqual(p.samples,1);p.close()
    def test_suppression_then_low_load_resumes_without_rebaseline(self):
        p,api=self.probe();previous=p.previous
        p.sample(dict(system_cpu_percent=95.))
        self.assertIs(p.previous,previous);self.assertIsNone(p.disabled_reason)
        row=p.sample(dict(system_cpu_percent=20.))
        self.assertTrue(row["available"]);self.assertEqual(api.calls,2);p.close()
    def test_unknown_cleanup_or_disabled_budget_never_promoted(self):
        p,api=self.probe(API(error=True));p.sample(dict(system_cpu_percent=90.))
        self.assertFalse(p.cleanup);self.assertFalse(p.close())
        self.assertEqual(p.summary()["native_capture_handle_cleanup_status"],"UNRESOLVED")
        p,api=self.probe(API(partial=True));calls=api.calls
        p.sample(dict(system_cpu_percent=90.));low=p.sample(dict(system_cpu_percent=20.))
        self.assertFalse(low["available"]);self.assertEqual(api.calls,calls)
        self.assertEqual(p.disabled_reason,"MEASUREMENT_COST_BUDGET_EXCEEDED");p.close()
    def test_owner_and_invalid_original_CPU_cannot_bypass_checks(self):
        p,api=self.probe();p.identity=lambda:(2,2)
        with self.assertRaises(ValueError):p.sample(dict(system_cpu_percent=90.))
        p,api=self.probe()
        for bad in (True,float("nan"),-1.,101.):
            with self.assertRaises(ValueError):p.sample(dict(system_cpu_percent=bad))
        self.assertEqual(api.calls,1);p.close()
    def test_original_cost_owner_factory_and_limits_not_changed(self):
        p,api=self.probe();row=p.summary()
        self.assertEqual(row["backend"],m.BACKEND)
        self.assertEqual(row["maximum_sample_budget_seconds"],.05)
        self.assertEqual(row["total_added_sample_budget_seconds"],2.)
        self.assertEqual(row["maximum_query_calls"],128)
        self.assertEqual(row["capture_api_source"],"tools/p09/bounded_cpu_attribution_probe_v2.py")
        self.assertFalse(row["original_CPU_RAM_guards_replaced"])
        self.assertFalse(row["PC_freeze_resolved"]);p.close()

if __name__=="__main__":unittest.main()
