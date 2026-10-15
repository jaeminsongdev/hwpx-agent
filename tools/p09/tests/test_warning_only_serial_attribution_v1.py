"""Deterministic observer equivalence, not product/Native runtime acceptance."""
import unittest
from unittest.mock import patch
import warning_only_serial_attribution_v1 as subject
import serial_observer_attribution as old
import conservative_maintenance as c


class Original:
    def __init__(self):
        self.processors=16;self.last=(100,200,100);self.cpu=20.0
        self.ram=50.0;self.commit=40.0;self.error=None;self.original_calls=0
    def sample(self):
        self.original_calls+=1
        if self.error:
            raise ValueError(self.error)
        self.last=tuple(x+100 for x in self.last)
        return dict(system_cpu_percent=self.cpu,available_ram_percent=self.ram,
            commit_used_percent=self.commit)


class Probe:
    def __init__(self,processors):
        self.calls=0;self.closes=0;self.ok=True
    def sample(self):
        self.calls+=1
        return dict(available=True,values={"fixed":"fixture"},
            interval_seconds=42.0,identical_to_original_K32_interval=False)
    def close(self):
        self.closes+=1;return self.ok
    def summary(self):
        return dict(samples=self.calls,cleanup_confirmed=self.ok)


class WarningOnlyContracts(unittest.TestCase):
    def make(self):
        self.now=0.0;self.objects=[]
        return subject.windows_type(Original,self.objects,
            factory=Probe,clock=lambda:self.now)()

    def test_all_cold_windows_do_not_start_any_sample_query(self):
        window=self.make()
        for i in range(80):
            self.now=i*.5;row=window.sample()
            self.assertIsNone(row["serial_cpu_attribution"]["values"])
            self.assertFalse(row["serial_cpu_attribution"]["fresh_for_this_original_resource_sample"])
        self.assertEqual(window.attribution_probe.calls,0)
        self.assertEqual(window.warning_only_cold_skips,80)
        self.assertEqual(window.original_calls,80)

    def test_original_observer_five_cold_queries_become_zero_without_skipping_K32(self):
        window=self.make();older=[]
        comparison=old.windows_type(Original,older,factory=Probe,clock=lambda:self.now)()
        for i in range(80):
            self.now=i*.5
            new=window.sample();previous=comparison.sample()
            for key in ("system_cpu_percent","available_ram_percent","commit_used_percent"):
                self.assertEqual(new[key],previous[key])
        self.assertEqual(comparison.attribution_probe.calls,5)
        self.assertEqual(window.attribution_probe.calls,0)
        self.assertEqual(window.original_calls,comparison.original_calls)

    def test_threshold_75_calls_exact_same_probe_not_a_cached_zero(self):
        window=self.make();window.cpu=74.99;window.sample()
        self.assertEqual(window.attribution_probe.calls,0)
        window.cpu=75.0;row=window.sample()
        self.assertEqual(window.attribution_probe.calls,1)
        self.assertTrue(row["serial_cpu_attribution"]["fresh_for_this_original_resource_sample"])
        window.cpu=91.67;window.sample()
        self.assertEqual(window.attribution_probe.calls,2)

    def test_original_half_second_and_real_long_PDH_interval_never_conflated(self):
        window=self.make();window.cpu=91.67
        diagnostic=window.sample()["serial_cpu_attribution"]
        self.assertEqual(diagnostic["interval_seconds"],42.0)
        self.assertFalse(diagnostic["identical_to_original_K32_interval"])
        self.assertFalse(diagnostic["long_interval_relabelled_as_K32_half_second"])
        self.assertFalse(diagnostic["causal_trigger_attribution_established"])

    def test_source_stop_tail_only_actual_warning_forces_query(self):
        window=self.make()
        for cpu in (5.47,7.5,27.77,91.67):
            window.cpu=cpu;window.sample()
        self.assertEqual(window.attribution_probe.calls,1)
        self.assertEqual(window.original_calls,4)

    def test_original_sample_error_propagates_without_probe_call(self):
        window=self.make();window.error="CPU_SAMPLE_INTERVAL_MISSING"
        with self.assertRaisesRegex(ValueError,"CPU_SAMPLE_INTERVAL_MISSING"):
            window.sample()
        self.assertEqual(window.attribution_probe.calls,0)

    def test_hard_low_ram_skips_optional_query_but_original_decision_unchanged(self):
        window=self.make();window.cpu=90.0;window.ram=4.99
        row=window.sample()
        self.assertEqual(c.decision(row,0),(0,"STOP_LOW_AVAILABLE_RAM"))
        self.assertEqual(window.attribution_probe.calls,0)
        self.assertEqual(window.warning_only_hard_skips,1)

    def test_hard_commit_skips_optional_query_before_stop(self):
        window=self.make();window.cpu=90.0;window.commit=95.0
        row=window.sample()
        self.assertEqual(c.decision(row,0),(0,"STOP_SYSTEM_COMMIT_PRESSURE"))
        self.assertEqual(window.attribution_probe.calls,0)

    def test_original_consecutive_cpu_emergency_decision_is_not_changed(self):
        window=self.make();window.cpu=100.0;row=window.sample()
        self.assertEqual(c.decision(row,3),(4,"STOP_SUSTAINED_SYSTEM_CPU"))
        self.assertEqual(window.original_calls,1)

    def test_split_uses_existing_same_system_time_tuple(self):
        window=self.make();row=window.sample()
        self.assertEqual(row["existing_system_time_breakdown"],old.split((100,200,100),(200,300,200)))
        self.assertFalse(row["existing_system_time_breakdown"]["extra_system_time_query"])

    def test_close_failure_remains_false_and_one_observer_only(self):
        window=self.make();window.attribution_probe.ok=False
        self.assertFalse(subject.close(self.objects))
        report=subject.summary(self.objects)
        self.assertEqual(report["existing_observer_instances"],1)
        self.assertFalse(report["probes"][0]["cleanup_confirmed"])
        self.assertFalse(report["runtime_connection_qualified"])

    def test_summary_never_claims_product_or_native_performance_improvement(self):
        self.make();report=subject.summary(self.objects)
        self.assertFalse(report["measured_Native_CPU_or_PC_freeze_improvement_proven"])
        self.assertFalse(report["second_sampler_thread_or_process"])

    def test_default_windows_and_probe_module_classes_are_not_mutated(self):
        original=subject.original.windows_type;before=c.Windows
        self.make()
        self.assertIs(c.Windows,before);self.assertIs(subject.original.windows_type,original)

    def test_no_thread_or_subprocess_even_at_warning(self):
        with patch("subprocess.Popen",side_effect=AssertionError("NO_CHILD")),patch(
            "threading.Thread.start",side_effect=AssertionError("NO_SAMPLER")):
            window=self.make();window.cpu=91.67;window.sample()
            self.assertTrue(subject.close(self.objects))

    def test_factory_clock_and_owner_must_be_explicit(self):
        with self.assertRaisesRegex(ValueError,"EXPLICIT_FACTORY_CLOCK_OWNER"):
            subject.windows_type(Original,[],factory=None,clock=lambda:0.0)
