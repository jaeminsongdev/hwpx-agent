import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import serial_observer_attribution as o
import accept_case112_current_epoch as a


class Original:
    def __init__(self):self.processors=16;self.last=(100,200,100);self.cpu=20.;self.error=None
    def sample(self):
        if self.error:raise ValueError(self.error)
        self.last=tuple(v+100 for v in self.last)
        return dict(system_cpu_percent=self.cpu,available_ram_percent=30.,commit_used_percent=40.)


class Probe:
    def __init__(self,processors):self.calls=0;self.closes=0;self.ok=True
    def sample(self):self.calls+=1;return dict(available=True,values={'fixed':'fixture'})
    def close(self):self.closes+=1;return self.ok
    def summary(self):return dict(samples=self.calls,cleanup_confirmed=self.ok)


class ObserverContracts(unittest.TestCase):
    def make(self):
        self.now=0.;self.objects=[]
        cls=o.windows_type(Original,self.objects,factory=Probe,clock=lambda:self.now)
        return cls()
    def test_original_values_and_resource_decisions_not_replaced(self):
        window=self.make();row=window.sample()
        self.assertEqual(row['system_cpu_percent'],20)
        self.assertEqual(a.c.decision(row,0),(0,None))
        window.cpu=100;row=window.sample()
        self.assertEqual(a.c.decision(row,3),(4,'STOP_SUSTAINED_SYSTEM_CPU'))
    def test_original_sampler_failure_not_masked_by_diagnostic(self):
        window=self.make();window.error='CPU_SAMPLE_INTERVAL_MISSING'
        with self.assertRaisesRegex(ValueError,'CPU_SAMPLE_INTERVAL_MISSING'):window.sample()
        self.assertEqual(window.attribution_probe.calls,0)
    def test_cold_eight_seconds_and_warning_forces_fresh_no_fake_cached_zero(self):
        window=self.make();window.sample();self.now=.5;row=window.sample()
        self.assertIsNone(row['serial_cpu_attribution']['values'])
        self.assertFalse(row['serial_cpu_attribution']['fresh_for_this_original_resource_sample'])
        window.cpu=90;row=window.sample()
        self.assertTrue(row['serial_cpu_attribution']['fresh_for_this_original_resource_sample'])
        self.assertEqual(window.attribution_probe.calls,2)
        window.cpu=20;self.now=8.5;window.sample();self.assertEqual(window.attribution_probe.calls,3)
    def test_breakdown_uses_same_tuples_no_new_native_query(self):
        row=o.split((100,200,100),(150,350,200))
        self.assertEqual(row['kernel_busy_machine_percent'],40)
        self.assertEqual(row['user_machine_percent'],40)
        self.assertFalse(row['extra_system_time_query'])
        self.assertIsNone(o.split((1,2,3),(1,2,3)))
    def test_one_observer_instance_and_cleanup_failure_visible(self):
        window=self.make();self.assertEqual(len(self.objects),1)
        window.attribution_probe.ok=False;self.assertFalse(o.close(self.objects))
        self.assertFalse(o.summary(self.objects)['probes'][0]['cleanup_confirmed'])
        self.assertFalse(o.summary(self.objects)['second_sampler_thread_or_process'])


if __name__=='__main__':
    guard=a.Guard();result=None
    try:
        guard.acquire();result=unittest.TextTestRunner(verbosity=1).run(unittest.defaultTestLoader.loadTestsFromTestCase(ObserverContracts))
    finally:guard.close()
    print(json.dumps(dict(contract_count=result.testsRun if result else 0,passed=bool(result and result.wasSuccessful()),
        cleanup_confirmed=guard.cleanup,actual_PDH_queries=False,product_child_executed=False)))
    raise SystemExit(0 if result and result.wasSuccessful() and guard.cleanup else 2)
