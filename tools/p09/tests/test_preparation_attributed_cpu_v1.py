import copy
import json
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import patch
import unittest

MODULE=None
REPLAY_PATH="implementation/p09/evidence/p09-361-case165-successor-recovery-preflight-run008-attempt004.v1.json"


def row(cpu=30,parent=.1):return dict(system_cpu_percent=cpu,parent_cpu_machine_percent=parent)


def windows(allowed=1,mask=1,priority=0x4000,read=True):
    def affinity(handle,a,s):a._obj.value=allowed;s._obj.value=65535;return read
    return NS(mask=mask,processors=16,k=NS(GetCurrentProcess=lambda:123,
        GetProcessAffinityMask=affinity,GetPriorityClass=lambda handle:priority))


class Original:
    def __init__(self):
        self.windows=windows();self.samples=[];self.last=0.;self.calls=0;self.row=row()
        self.error=None;self.cached=False;self.cleanup=False
    def check(self,force=False):
        self.calls+=1
        if self.error:raise ValueError(self.error)
        if not self.cached:self.samples.append(dict(self.row));self.last+=.5
        return "original-result"
    def close(self):self.cleanup=True


class Tests(unittest.TestCase):
    def state(self):return MODULE.State(16,"whole_metadata_preflight")
    def guard(self):return MODULE.guard_type(Original,role="whole_metadata_preflight")()

    def test_below_warning_first_missing_attribution_is_not_an_excuse_to_skip_original(self):
        state=self.state();self.assertEqual(state.observe(1,0.,row(30,None)),"BELOW_SYSTEM_WARNING")
        self.assertEqual(state.observe(2,.5,row()),"BELOW_SYSTEM_WARNING")

    def test_isolated_75_warning_low_owned_load_is_recorded_not_stop(self):
        state=self.state();self.assertEqual(state.observe(1,0.,row(75,.1)),"WARNING_LOW_OWNED_LOAD")
        self.assertEqual(state.warning_samples,1);self.assertFalse(state.stopped)

    def test_below_90_single_warning_remains_bounded(self):
        state=self.state();state.observe(1,0.,row(89.999,.1));self.assertFalse(state.stopped)

    def test_exact_90_stops_immediately_and_latches(self):
        state=self.state()
        with self.assertRaisesRegex(ValueError,"STOP_PREPARATION_SYSTEM_PRESSURE90"):state.observe(1,0.,row(90,None))
        with self.assertRaisesRegex(ValueError,"STOP_LATCHED"):state.observe(2,.5,row())

    def test_four_fresh_warning_samples_over_1p5_seconds_span_stop(self):
        state=self.state()
        for i in range(3):state.observe(i+1,i*.5,row(75,.1))
        with self.assertRaisesRegex(ValueError,"SUSTAINED_SYSTEM_PRESSURE75"):state.observe(4,1.5,row(75,.1))
        self.assertTrue(state.stopped)

    def test_one_fresh_normal_sample_resets_system_warning_run(self):
        state=self.state()
        for i,cpu in enumerate((80,80,30,80,80,80)):state.observe(i+1,i*.5,row(cpu,.1))
        self.assertEqual(state.warning_run,3);self.assertFalse(state.stopped)

    def test_thousand_cached_checkpoints_do_not_make_one_warning_sustained(self):
        state=self.state();sample=row(80,.1);state.observe(1,0.,sample)
        for _ in range(1000):state.observe(1,0.,sample)
        self.assertEqual((state.decisions,state.warning_run,state.warning_samples),(1,1,1))

    def test_cached_sample_mutation_rejected_and_latched(self):
        state=self.state();state.observe(1,0.,row())
        with self.assertRaisesRegex(ValueError,"CACHED_SAMPLE_NOT_MUTATED"):state.observe(1,0.,row(40,.1))
        self.assertTrue(state.stopped)

    def test_sample_skips_rollback_and_nonmonotonic_time_fail_closed(self):
        for index,stamp in ((3,.5),(0,.5),(2,0.),(2,-1.)):
            state=self.state();state.observe(1,0.,row())
            with self.subTest(index=index,stamp=stamp),self.assertRaises(ValueError):state.observe(index,stamp,row())
            self.assertTrue(state.stopped)

    def test_invalid_cpu_or_owned_samples_fail_closed(self):
        for field in ("system_cpu_percent","parent_cpu_machine_percent"):
            for value in (True,"30",float("nan"),float("inf"),-1,101):
                state=self.state();sample=row();sample[field]=value
                with self.subTest(field=field,value=repr(value)),self.assertRaises(ValueError):state.observe(1,0.,sample)
                self.assertTrue(state.stopped)

    def test_missing_attribution_cannot_excuse_high_first_or_later_load(self):
        state=self.state()
        with self.assertRaisesRegex(ValueError,"CPU_ATTRIBUTION_MISSING"):state.observe(1,0.,row(75,None))
        state=self.state();state.observe(1,0.,row(30,None))
        with self.assertRaisesRegex(ValueError,"CPU_ATTRIBUTION_MISSING"):state.observe(2,.5,row(30,None))

    def test_two_owned_overload_samples_stop_even_when_system_is_below_warning(self):
        state=self.state();self.assertEqual(state.owned_limit,7.8125)
        state.observe(1,0.,row(30,8))
        with self.assertRaisesRegex(ValueError,"OWNED_CPU_OVERLOAD"):state.observe(2,.5,row(30,8))

    def test_owned_overload_counter_resets_and_exact_limit_is_allowed(self):
        state=self.state()
        for i,value in enumerate((8,state.owned_limit,8)):state.observe(i+1,i*.5,row(30,value))
        self.assertEqual(state.owned_run,1);self.assertFalse(state.stopped)

    def test_four_rapid_fake_fresh_samples_cannot_claim_a_sustained_window(self):
        state=self.state()
        for i in range(3):state.observe(i+1,i*.1,row(80,.1))
        with self.assertRaisesRegex(ValueError,"SAMPLE_CADENCE_INVALID"):state.observe(4,.3,row(80,.1))

    def test_only_preparation_roles_and_bounded_processor_counts(self):
        for value in (True,0,65,"16"):
            with self.assertRaises(ValueError):MODULE.State(value,"whole_metadata_preflight")
        for role in ("Native","product",None,True):
            with self.assertRaises(ValueError):MODULE.guard_type(Original,role=role)

    def test_original_hard_error_precedes_policy_and_remains_latched(self):
        g=self.guard();g.error="ORIGINAL_RAM_COMMIT_OR_DEADLINE_STOP";g.row=row(100,99)
        with self.assertRaisesRegex(ValueError,"^ORIGINAL_RAM_COMMIT_OR_DEADLINE_STOP$"):g.check()
        self.assertEqual(g.preparation_CPU.decisions,0);g.error=None
        with self.assertRaisesRegex(ValueError,"STOP_LATCHED"):g.check()
        self.assertEqual(g.calls,1);g.close();self.assertTrue(g.cleanup)

    def test_guard_preserves_return_sampling_cache_and_unconditional_cleanup(self):
        g=self.guard();g.row=row(80,.1)
        self.assertEqual(g.check(),"original-result");g.cached=True
        for _ in range(10):g.check()
        self.assertEqual(len(g.samples),1);self.assertEqual(g.preparation_CPU.decisions,1)
        self.assertIs(type(g).close,Original.close);g.close();self.assertTrue(g.cleanup)

    def test_actual_owned_limit_API_contract_and_wrong_limits_rejected(self):
        result=MODULE.owned_limits(windows());self.assertTrue(result["readback_verified"])
        for w in (windows(read=False),windows(allowed=3,mask=3),windows(allowed=2),windows(priority=0x20)):
            with self.assertRaises(ValueError):MODULE.owned_limits(w)

    def test_original_75_guard_and_global_host_policy_are_unchanged(self):
        import terminal_metadata_pressure_v1 as old
        import conservative_maintenance as c
        policy=dict(c.POLICY);original_check=Original.check
        self.guard().check();self.assertIs(Original.check,original_check);self.assertEqual(c.POLICY,policy)
        g=old.guard_type(Original)();g.row=row(75,.1)
        with self.assertRaisesRegex(ValueError,"STOP_TERMINAL_METADATA_WARNING"):g.check()

    def test_actual_failed_pref4_sample_replay_is_not_a_new_run_or_PASS(self):
        root=Path(__file__).resolve().parents[3];record=json.loads((root/REPLAY_PATH).read_text(encoding="utf-8"))
        before=copy.deepcopy(record);state=self.state();samples=record["resource_samples"]
        start=datetime.fromisoformat(samples[0]["time_utc"]).timestamp()
        for i,sample in enumerate(samples):
            stamp=datetime.fromisoformat(sample["time_utc"]).timestamp()-start
            state.observe(i+1,stamp,sample)
        self.assertEqual(record,before);self.assertEqual(record["state"],"FAILED_CURRENT_SUCCESSOR_PREFLIGHT_NOT_ADOPTED")
        self.assertEqual(state.decisions,len(samples));self.assertGreaterEqual(state.warning_samples,1)
        self.assertFalse(state.stopped);self.assertFalse(state.summary()["GO_authorized"])
