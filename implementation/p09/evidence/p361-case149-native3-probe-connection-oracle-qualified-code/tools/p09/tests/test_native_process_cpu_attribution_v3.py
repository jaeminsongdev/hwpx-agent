import sys
import unittest
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import native_process_cpu_attribution_v3 as backend


class API:
    def __init__(self,partial=False,error=False):
        self.partial=partial;self.error=error;self.calls=0
    def capture(self):
        self.calls+=1
        if self.error:raise ValueError("SNAPSHOT_CLOSE")
        return dict(time_monotonic=float(self.calls),rows={},enumerated=0,unavailable=0,truncated=False,
          collection_seconds=.01,measurement_budget_exceeded=self.partial)
class Clock:
    def __init__(self,step=.01):self.n=0.;self.step=step
    def __call__(self):self.n+=self.step;return self.n


class Tests(unittest.TestCase):
    def test_new_backend_and_capture_source_provenance(self):
        p=backend.Probe(16,api=API(),clock=Clock(),identity=lambda:(1,1))
        s=p.summary()
        self.assertEqual(s["backend"],"NATIVE_TOOLHELP_PROCESS_TIMES_V3")
        self.assertEqual(s["capture_api_source"],"tools/p09/bounded_cpu_attribution_probe_v2.py")
        self.assertEqual(s["maximum_sample_budget_seconds"],.05)
        self.assertEqual(s["total_added_sample_budget_seconds"],2.)
        self.assertEqual(s["maximum_query_calls"],128)
        p.close()

    def test_partial_first_capture_not_baseline_and_no_retry(self):
        api=API(partial=True);p=backend.Probe(16,api=api,clock=Clock(),identity=lambda:(1,1))
        self.assertIsNone(p.previous)
        self.assertEqual(p.disabled_reason,"MEASUREMENT_COST_BUDGET_EXCEEDED")
        self.assertTrue(p.close())
        self.assertIsNone(p.capture());self.assertEqual(api.calls,1)
        self.assertEqual(p.summary()["partial_captures_discarded"],1)

    def test_later_partial_does_not_publish_zero_or_partial_values(self):
        api=API();p=backend.Probe(16,api=api,clock=Clock(),identity=lambda:(1,1));api.partial=True
        row=p.sample(dict(system_cpu_percent=60.))
        self.assertFalse(row["available"]);self.assertIsNone(row["values"])
        self.assertIsNone(p.previous);self.assertTrue(p.cleanup)

    def test_handle_failure_cleanup_unknown_unchanged(self):
        p=backend.Probe(16,api=API(error=True),clock=Clock(),identity=lambda:(1,1))
        self.assertFalse(p.cleanup);self.assertFalse(p.close())
        self.assertEqual(p.summary()["native_capture_handle_cleanup_status"],"UNRESOLVED")
        self.assertTrue(p.summary()["capture_failure_cleanup_unknown"])

    def test_api_constructor_is_in_setup_budget(self):
        clock=Clock();api=API()
        def create():clock.n+=.06;return api
        with patch.object(backend.native,"Snapshot",side_effect=create):
            p=backend.Probe(16,clock=clock,identity=lambda:(1,1))
        self.assertGreater(p.maximum_latency,.05)
        self.assertEqual(p.disabled_reason,"MEASUREMENT_COST_BUDGET_EXCEEDED")
        self.assertIsNone(p.previous)

    def test_same_owner_and_original_sample_bytecode(self):
        current=[(1,1)]
        p=backend.Probe(16,api=API(),clock=Clock(),identity=lambda:current[0])
        self.assertIs(p.sample.__func__.__code__,backend.prior.prior.Probe.sample.__code__)
        current[0]=(2,2)
        with self.assertRaises(ValueError):p.capture()
        p.close()


if __name__=="__main__":unittest.main()
