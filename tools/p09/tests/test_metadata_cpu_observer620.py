import unittest
from types import SimpleNamespace as NS
import metadata_cpu_observer620 as m
class Window:
    processors=16
    def __init__(self):self.last=(100,200,300);self.cpu=20.;self.calls=0
    def sample(self):
        self.calls+=1;self.last=tuple(v+10 for v in self.last)
        return dict(system_cpu_percent=self.cpu,available_ram_percent=40.,commit_used_percent=50.)
class Probe:
    def __init__(self,processors):self.cleanup=True;self.samples=[];self.processors=processors
    def sample(self,row):self.samples.append(dict(row));return dict(available=False,values=None,reason='TEST_ONLY_UNAVAILABLE')
    def close(self):return self.cleanup
    def summary(self):return dict(samples=len(self.samples),cleanup_confirmed=self.cleanup)
class Tests(unittest.TestCase):
    def attach(self):
        window=Window();clock=[0.];adapter=m.Attached(NS(windows=window),factory=Probe,clock=lambda:clock[0]);return window,adapter,clock
    def test_exact_original_values_and_single_original_sample_are_retained(self):
        w,a,t=self.attach();row=w.sample();self.assertEqual(w.calls,1);self.assertEqual(row['system_cpu_percent'],20.);self.assertEqual(row['available_ram_percent'],40.);self.assertEqual(row['commit_used_percent'],50.);a.close()
    def test_cold_interval_does_not_add_queries_or_zero_values(self):
        w,a,t=self.attach();w.sample();t[0]=7.99;row=w.sample();self.assertEqual(len(a.probe.samples),1);self.assertIsNone(row['serial_cpu_attribution']['values']);t[0]=8.;w.sample();self.assertEqual(len(a.probe.samples),2);a.close()
    def test_warning_is_passed_unchanged_to_original_v4_suppression_policy(self):
        w,a,t=self.attach();w.sample();w.cpu=95.;t[0]=1.;row=w.sample();self.assertEqual(row['system_cpu_percent'],95.);self.assertEqual(a.probe.samples[-1]['system_cpu_percent'],95.);a.close()
    def test_close_restores_instance_and_never_changes_global_class(self):
        original=Window.sample;w,a,t=self.attach();self.assertIn('sample',vars(w));self.assertTrue(a.close());self.assertNotIn('sample',vars(w));self.assertIs(Window.sample,original);self.assertTrue(a.close());self.assertEqual(w.sample()['system_cpu_percent'],20.)
    def test_existing_instance_method_is_restored_exactly(self):
        w=Window();original=w.sample;w.sample=original;a=m.Attached(NS(windows=w),factory=Probe);a.close();self.assertIs(vars(w)['sample'],original)
    def test_unknown_probe_cleanup_is_not_promoted(self):
        w,a,t=self.attach();a.probe.cleanup=False;self.assertFalse(a.close());self.assertFalse(a.summary()['backend']['cleanup_confirmed']);self.assertTrue(a.closed)
    def test_original_error_propagates_without_an_extra_process_query(self):
        w=Window()
        def fail():raise ValueError('ORIGINAL_RESOURCE_ERROR')
        w.sample=fail;a=m.Attached(NS(windows=w),factory=Probe)
        with self.assertRaisesRegex(ValueError,'ORIGINAL_RESOURCE_ERROR'):w.sample()
        self.assertFalse(a.probe.samples);a.close()
    def test_duplicate_attachment_cannot_stack_observers(self):
        w,a,t=self.attach()
        with self.assertRaises(ValueError):m.Attached(NS(windows=w),factory=Probe)
        a.close()
