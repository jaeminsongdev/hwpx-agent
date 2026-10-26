import json,unittest
from types import SimpleNamespace as NS
import resource_bundle714 as m

class Window:
    processors=16
    def __init__(self):self.calls=0;self.cpu=20.;self.fail=False
    def sample(self):
        self.calls+=1
        if self.fail:raise ValueError('ORIGINAL_RESOURCE_ERROR')
        return dict(system_cpu_percent=self.cpu,available_ram_percent=40.,commit_used_percent=50.)
class Probe:
    cleanup=True
class Observer:
    def __init__(self,guard):
        self.window=guard.windows;self.before=self.window.sample;self.had='sample'in vars(self.window)
        self.saved=vars(self.window).get('sample');self.probe=Probe();self.calls=0;self.closed=False
        def sample():
            row=self.before();self.calls+=1
            row['serial_cpu_attribution']=dict(available=False,values=None,
                reason='HOST_CPU_WARNING_OPTIONAL_ATTRIBUTION_SUPPRESSED'if row['system_cpu_percent']>=75 else'FIXTURE_ONLY_UNAVAILABLE')
            return row
        self.window.sample=sample
    def close(self):
        if self.had:self.window.sample=self.saved
        else:del self.window.sample
        self.closed=True;return self.probe.cleanup
    def summary(self):return dict(samples=self.calls,closed=self.closed,cleanup=self.probe.cleanup)
class Tests(unittest.TestCase):
    def create(self):
        guard=NS(windows=Window(),samples=[]);stamp=[100.]
        journal=m.Attached(guard,factory=Observer,clock=lambda:stamp[0]);return guard,journal,stamp
    def take(self,g,t,at,**late):
        t[0]=at;row=g.windows.sample();row.update(late);g.samples.append(row);return row
    def unpack(self,value):return[dict(zip(value['shapes'][i],values,strict=True))for i,values in value['rows']]
    def test_one_original_sampler_and_no_phase_triggered_queries(self):
        g,a,t=self.create();a.phase('tests');self.assertEqual(g.windows.calls,0)
        row=self.take(g,t,100.5);self.assertEqual(g.windows.calls,1)
        self.assertEqual((row['system_cpu_percent'],row['available_ram_percent'],row['commit_used_percent']),(20.,40.,50.))
        self.assertEqual(row['verification_phase714'],'tests');self.assertEqual(row['resource_observation_interval714'],.5);a.close()
    def test_warning_unavailable_and_original100_are_preserved_without_zero_substitution(self):
        g,a,t=self.create();g.windows.cpu=100.;row=self.take(g,t,100.5)
        self.assertEqual(row['system_cpu_percent'],100.);self.assertIsNone(row['serial_cpu_attribution']['values'])
        self.assertIn('SUPPRESSED',row['serial_cpu_attribution']['reason']);a.close()
        self.assertEqual(self.unpack(a.packet()),g.samples)
    def test_late_parent_job_fields_missing_and_none_round_trip_losslessly(self):
        g,a,t=self.create();self.take(g,t,100.5,parent_cpu_machine_percent=None)
        a.phase('readback');self.take(g,t,101.,peak_job_private_percent=2.5)
        a.close();p=json.loads(json.dumps(a.packet()))
        self.assertEqual(self.unpack(p),g.samples)
        self.assertEqual(p['original_sampler_calls'],2);self.assertEqual(len(p['shapes']),2)
        self.assertFalse(p['original_CPU_RAM_decisions_or_cadence_changed'])
    def test_original_guard_error_is_propagated_before_any_record(self):
        g,a,t=self.create();g.windows.fail=True
        with self.assertRaisesRegex(ValueError,'ORIGINAL_RESOURCE_ERROR'):g.windows.sample()
        self.assertEqual(a.calls,0);self.assertEqual(a.observer.calls,0);self.assertEqual(g.samples,[]);a.close()
    def test_phase_labels_are_closed_and_raw_paths_cannot_be_recorded(self):
        g,a,t=self.create()
        with self.assertRaises(ValueError):a.phase('C:/private/source.hwpx')
        self.assertEqual(g.windows.calls,0);a.close()
        with self.assertRaises(ValueError):a.phase('tests')
    def test_close_restores_only_this_instance_and_preserves_failed_cleanup(self):
        original=Window.sample;g,a,t=self.create();a.observer.probe.cleanup=False
        self.assertFalse(a.close());self.assertIs(Window.sample,original);self.assertNotIn('sample',vars(g.windows))
        self.assertFalse(a.close());self.assertTrue(a.packet()['closed']);self.assertFalse(a.packet()['observer']['cleanup'])
    def test_duplicate_attach_cannot_stack_and_existing_instance_override_is_restored(self):
        g,a,t=self.create()
        with self.assertRaises(ValueError):m.Attached(g,factory=Observer)
        a.close();g.windows.sample=g.windows.sample;before=g.windows.sample
        b=m.Attached(g,factory=Observer);b.close();self.assertIs(g.windows.sample,before)
    def test_extra_samples_and_nonfinite_clock_are_rejected(self):
        g,a,t=self.create();g.samples.append({})
        with self.assertRaises(ValueError):a.packet()
        g.samples.clear();t[0]=float('nan')
        with self.assertRaises(ValueError):g.windows.sample()
        self.assertEqual(a.calls,0);a.close()
    def test_output_budget_is_explicit_without_truncation_or_field_removal(self):
        g,a,t=self.create();self.take(g,t,100.5,fixture_padding='x'*(m.MAX_BYTES+1));a.close()
        with self.assertRaisesRegex(ValueError,'LOSSLESS_OUTPUT_LIMIT'):a.packet()
        self.assertIn('fixture_padding',g.samples[0])
if __name__=='__main__':unittest.main()
