import sys
import unittest
from pathlib import Path
from types import SimpleNamespace as NS

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import native_process_cpu_attribution_v2 as backend


class Clock:
    now=0.
    def __call__(self):return self.now


class API:
    def __init__(self,clock):self.clock=clock;self.fail=False;self.delay=.001;self.calls=0
    def capture(self):
        self.calls+=1;self.clock.now+=self.delay
        if self.fail:raise ValueError("CPU_ATTRIBUTION_PROCESS_HANDLE_CLOSE")
        return dict(time_monotonic=self.clock.now,collection_seconds=self.delay,rows={},unavailable=1,truncated=False)


class Tests(unittest.TestCase):
    def test_setup_exception_cleanup_unknown(self):
        clock=Clock();api=API(clock);api.fail=True
        p=backend.Probe(16,api=api,clock=clock)
        self.assertFalse(p.close())
        self.assertTrue(p.summary()["capture_failure_cleanup_unknown"])

    def test_sample_exception_never_cleanup_PASS_or_retry(self):
        clock=Clock();api=API(clock);p=backend.Probe(16,api=api,clock=clock)
        api.fail=True;out=p.sample(dict(system_cpu_percent=0))
        self.assertFalse(out["available"]);self.assertFalse(p.close())
        api.fail=False;p.sample(dict(system_cpu_percent=0));self.assertEqual(api.calls,2)

    def test_closed_slow_budget_still_clean(self):
        clock=Clock();api=API(clock);p=backend.Probe(16,api=api,clock=clock)
        api.delay=.051;p.sample(dict(system_cpu_percent=0))
        self.assertEqual(p.disabled_reason,"MEASUREMENT_COST_BUDGET_EXCEEDED")
        self.assertTrue(p.close());self.assertFalse(p.capture_failure_cleanup_unknown)

    def test_all_owners_closed_even_if_first_unknown(self):
        calls=[]
        class Probe:
            def __init__(self,name,result):self.name=name;self.result=result
            def close(self):calls.append(self.name);return self.result
        self.assertFalse(backend.close([NS(attribution_probe=Probe("first",False)),NS(attribution_probe=Probe("second",True))]))
        self.assertEqual(calls,["first","second"])

    def test_successful_v1_sampling_unchanged_and_private_defaults(self):
        clock=Clock();api=API(clock);p=backend.Probe(16,api=api,clock=clock);clock.now+=2
        out=p.sample(dict(system_cpu_percent=20));self.assertTrue(out["available"])
        self.assertEqual(out["values"]["total_cpu"],20)
        self.assertIsNone(out["values"]["DPC_cpu"])
        self.assertTrue(p.close());self.assertIsNot(backend.Probe,backend.prior.Probe)
        self.assertEqual(backend.prior.Probe.sample.__code__,backend.Probe.sample.__code__)


if __name__=="__main__":unittest.main()
