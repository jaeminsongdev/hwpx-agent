import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import native_process_cpu_attribution_v1 as diagnostic


class Clock:
    now = 0.
    def __call__(self): return self.now


class API:
    def __init__(self, clock): self.clock=clock;self.calls=0;self.delay=.001;self.fail=False
    def capture(self):
        self.calls+=1;self.clock.now+=self.delay
        if self.fail:raise OSError("REDACTED")
        ticks=self.calls*10000000
        return dict(time_monotonic=self.clock.now,collection_seconds=self.delay,unavailable=1,truncated=False,
                    rows={4:dict(pid=4,parent=0,role="system",creation=1,ticks=ticks),
                          10:dict(pid=10,parent=0,role="msmpeng.exe",creation=2,ticks=ticks)})


class Tests(unittest.TestCase):
    def probe(self):
        clock=Clock();api=API(clock);identity=[(1,1)]
        probe=diagnostic.Probe(16,api=api,clock=clock,identity=lambda:identity[0])
        return probe,api,clock,identity

    def test_native_values_and_PID_creation_bound(self):
        p,api,clock,_=self.probe();clock.now+=2
        out=p.sample(dict(system_cpu_percent=25))
        self.assertEqual(out["values"]["total_cpu"],25)
        self.assertTrue(out["values"]["System"]["creation_identity_bound"])
        self.assertLess(out["values"]["System"]["machine_cpu_percent"],6.25)

    def test_DPC_IRQ_unavailable_not_zero(self):
        p,_,clock,_=self.probe();clock.now+=2
        out=p.sample(dict(system_cpu_percent=25))
        self.assertIsNone(out["values"]["DPC_cpu"])
        self.assertIsNone(out["values"]["interrupt_cpu"])
        self.assertFalse(out["coverage_complete"])

    def test_setup_cost_cap_included(self):
        clock=Clock();api=API(clock);api.delay=.051
        p=diagnostic.Probe(16,api=api,clock=clock)
        self.assertEqual(p.disabled_reason,"MEASUREMENT_COST_BUDGET_EXCEEDED")
        p.sample(dict(system_cpu_percent=100));self.assertEqual(api.calls,1)

    def test_slow_call_stops_without_resume(self):
        p,api,_,_=self.probe();api.delay=1.4
        out=p.sample(dict(system_cpu_percent=100))
        self.assertFalse(out["available"]);self.assertIsNone(out["values"])
        api.delay=.001;p.sample(dict(system_cpu_percent=0))
        self.assertEqual(api.calls,2)

    def test_total_cost_cap_unchanged(self):
        p,api,_,_=self.probe();p.total_latency=1.999
        api.delay=.002;p.sample(dict(system_cpu_percent=0))
        self.assertEqual(p.disabled_reason,"MEASUREMENT_COST_BUDGET_EXCEEDED")

    def test_query_cap(self):
        p,api,_,_=self.probe();p.queries=128
        p.sample(dict(system_cpu_percent=0));self.assertEqual(api.calls,1)
        self.assertEqual(p.disabled_reason,"QUERY_COUNT_BOUND")

    def test_owner_changes_rejected(self):
        p,_,_,identity=self.probe();identity[0]=(1,2)
        with self.assertRaisesRegex(ValueError,"SAME_OBSERVER_OWNER"):p.sample(dict(system_cpu_percent=0))

    def test_unavailable_query_stays_unavailable(self):
        p,api,_,_=self.probe();api.fail=True
        out=p.sample(dict(system_cpu_percent=0));self.assertFalse(out["available"])
        self.assertEqual(p.disabled_reason,"NATIVE_PROCESS_QUERY_UNAVAILABLE")

    def test_cold8_warning75_and_original_sample(self):
        clock=Clock();objects=[]
        class FakeProbe:
            calls=0
            def sample(self,row): self.calls+=1;return dict(available=False,values=None)
        class Original:
            def __init__(self):self.processors=16;self.last=(0,0,0);self.cpu=20;self.calls=0
            def sample(self):
                self.calls+=1;self.last=(self.calls,self.calls+1,self.calls+2)
                return dict(system_cpu_percent=self.cpu,available_ram_percent=50)
        window=diagnostic.windows_type(Original,objects,factory=lambda _:FakeProbe(),clock=clock)()
        self.assertEqual(window.sample()["available_ram_percent"],50)
        window.sample();self.assertEqual(window.attribution_probe.calls,1)
        clock.now=8;window.sample();self.assertEqual(window.attribution_probe.calls,2)
        window.cpu=75;window.sample();self.assertEqual(window.attribution_probe.calls,3)

    def test_original_error_prevents_query(self):
        objects=[]
        class FakeProbe:
            def sample(self,row):raise AssertionError("MUST_NOT_QUERY")
        class Original:
            def __init__(self):self.processors=16;self.last=(0,0,0)
            def sample(self):raise ValueError("ORIGINAL_ERROR")
        window=diagnostic.windows_type(Original,objects,factory=lambda _:FakeProbe())()
        with self.assertRaisesRegex(ValueError,"ORIGINAL_ERROR"):window.sample()

    def test_cleanup_and_truthful_summary(self):
        p,_,_,_=self.probe();p.close();s=p.summary()
        self.assertTrue(s["cleanup_confirmed"]);self.assertFalse(s["PDH_or_WMI_called"])
        self.assertFalse(s["runtime_connection_qualified"])


if __name__ == "__main__":unittest.main()
