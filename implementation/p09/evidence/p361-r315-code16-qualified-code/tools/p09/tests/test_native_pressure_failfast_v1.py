import ast
import math
import sys
import threading
import time
import unittest
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import native_pressure_failfast_v1 as m
import current_stored_native_bridge as native
import current_stored_runtime_scope as scope
import current_queue_acquisition_checkpoint as acquisition

ROOT=Path(__file__).resolve().parents[3]
RAW={key:(ROOT/pin["path"]).read_bytes() for key,pin in
    (("pressure",m.PRESSURE_PIN),("early",m.EARLY_PIN),("model",m.MODEL_PIN),("acquisition",m.ACQUISITION_PIN))}
C=NS(require=m.require,POLICY=dict(sample_seconds=.5))
P=native.definitions(RAW["pressure"].decode(),("PressureCheckpoint",),
    dict(c=C,math=math,time=time,WARNING_PERCENT=95,COOL_SAMPLES=2,MAX_PAUSE_WINDOWS=8)).PressureCheckpoint
E=native.definitions(RAW["early"].decode(),("EarlySourceCheckpoint",),
    dict(require=m.require,math=math,WARNING=90,COOL=2,MAX_WINDOWS=8,
        m=NS(entry=NS(locks=NS(time=time)),p=NS(c=C)))).EarlySourceCheckpoint

def original_model():
    tree=ast.parse(RAW["model"].decode());node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=="model")
    env=dict(require=m.require)
    exec(compile(ast.Module(body=[node],type_ignores=[]),m.MODEL_PIN["path"],"exec",dont_inherit=True),env)
    return env["model"]
def owner(cpu):return NS(lock=threading.Lock(),samples=[dict(system_cpu_percent=cpu)])
def checkpoint(early=False,cpu=20.,base=None):
    calls=[];sleeps=[];resources=owner(cpu)
    fn=base or (lambda:calls.append(1))
    New=m.checkpoint_type(E if early else P,RAW["early" if early else "pressure"],early=early)
    obj=New(fn,resources,sleep=lambda seconds:sleeps.append(seconds))
    return obj,calls,sleeps,resources

class Tests(unittest.TestCase):
    def test_low_pressure_original_callback_once_same_latest_method(self):
        obj,calls,sleeps,_=checkpoint();self.assertIsNone(obj());self.assertEqual(calls,[1]);self.assertEqual(sleeps,[])
        self.assertIs(type(obj).latest,P.latest);self.assertEqual(obj.summary()["completed_pause_windows"],0)
    def test_native95_warning_stops_before_sleep_without_resume(self):
        obj,calls,sleeps,resources=checkpoint(cpu=95.)
        with self.assertRaisesRegex(ValueError,"STOP_NATIVE_READ_PRESSURE_NO_COOLING"):obj()
        resources.samples[:]=[dict(system_cpu_percent=0.)]
        with self.assertRaisesRegex(ValueError,"STOP_LATCHED_NATIVE_PRESSURE"):obj()
        self.assertEqual(calls,[1]);self.assertEqual(sleeps,[]);self.assertEqual(obj.warning_entries,1)
    def test_source90_warning_stops_at_original_threshold(self):
        obj,calls,sleeps,_=checkpoint(early=True,cpu=90.)
        with self.assertRaisesRegex(ValueError,"STOP_NATIVE_SOURCE_PRESSURE_NO_COOLING"):obj()
        self.assertEqual(calls,[1]);self.assertEqual(sleeps,[]);self.assertEqual(obj.summary()["early_source_warning_CPU_percent"],90)
    def test_original_hard_error_precedes_pressure_error_and_retains_identity(self):
        error=ValueError("ORIGINAL_HARD_STOP")
        def fail():raise error
        obj,_,sleeps,_=checkpoint(cpu=100.,base=fail)
        with self.assertRaises(ValueError) as ctx:obj()
        self.assertIs(ctx.exception,error);self.assertEqual(sleeps,[]);self.assertEqual(obj.warning_entries,0)
    def test_invalid_sample_uses_original_latest_validation(self):
        for value in (None,float("nan"),101.,-1.,True):
            obj,calls,sleeps,_=checkpoint(cpu=value)
            with self.assertRaises(ValueError):obj()
            self.assertEqual(calls,[1]);self.assertEqual(sleeps,[])
    def test_no_sample_is_not_promoted_to_zero(self):
        obj,calls,_,resources=checkpoint();resources.samples.clear()
        with self.assertRaises(ValueError):obj()
        self.assertEqual(calls,[1])
    def test_source_below90_and_native_below95_retained(self):
        for early,cpu in ((True,89.99),(False,94.99)):
            obj,calls,sleeps,_=checkpoint(early,cpu);obj();self.assertEqual(calls,[1]);self.assertEqual(sleeps,[])
            self.assertFalse(obj.summary()["warning_latched"])
    def test_changed_original_source_and_code_rejected(self):
        with self.assertRaises(ValueError):m.checkpoint_type(P,RAW["pressure"]+b"\n")
        class Changed(P):
            def __call__(self):return None
        with self.assertRaises(ValueError):m.checkpoint_type(Changed,RAW["pressure"])
    def test_native_connection_pacer_and_all_other_api_identity_retained(self):
        class Locks:
            def __init__(self):
                self.open_pressure=P(lambda:None,owner(20.))
                self.api=NS(pacer=NS(checkpoint=self.open_pressure,rate=20,opens=0))
                self.phase_pacer=self.api.pacer;self.phase_checkpoint=self.open_pressure
                self.original_open_checkpoint=self.open_pressure
                self.saturation_checkpoint=NS(checkpoint=self.open_pressure)
            def summary(self):return dict(acquisition_source_warning_fail_fast=dict(byte_boundary_cooling_policy_changed=False))
            def acquire(self):return "original_acquire"
            def reader_sources(self):return "original_reader_sources"
            def close(self):return "original_close"
        old=NS(InputLocks=Locks,PressureCheckpoint=P,EarlySourceCheckpoint=E,frames=object())
        new=m.connect_api(old,RAW["pressure"],RAW["early"]);held=new.InputLocks()
        self.assertIs(held.api.pacer.checkpoint,held.open_pressure);self.assertEqual(held.api.pacer.rate,20)
        self.assertIs(new.frames,old.frames);self.assertIs(new.InputLocks.acquire,Locks.acquire)
        self.assertIs(new.InputLocks.reader_sources,Locks.reader_sources);self.assertIs(new.InputLocks.close,Locks.close)
        self.assertTrue(held.summary()["terminal_native_pressure_connection"]["all_locks_before_first_read_retained"])
        self.assertIs(old.PressureCheckpoint,P)
    def test_summary_truthfully_changes_cooling_fields_zero_not_legacy_two(self):
        for early in (False,True):
            obj,*_=checkpoint(early);row=obj.summary();self.assertFalse(row["cooling_or_resume_permitted"])
            self.assertEqual(row["requested_pause_seconds"],0);self.assertFalse(row["additional_sampler_or_native_query"])
            self.assertEqual(row["cool_distinct_samples" if early else "cool_distinct_sample_windows"],0)
    def test_exact_model_removes_only_four_actual_cooling_seconds(self):
        required={"a.exe":dict(path="a.exe",bytes=1048576,sha256="0"*64),"a.rs":dict(path="a.rs",bytes=2097152,sha256="1"*64)}
        old=original_model();new=m.model_projection(old,RAW["model"],scope)
        before=old(required,167);after=new(required,167)
        self.assertEqual(before["predicted_runtime_combined_seconds"]-after["predicted_runtime_combined_seconds"],4)
        for key in ("inputs","directories","binary_bytes","other_bytes","native_acquisition_seconds","two_actual_byte_pass_nominal_seconds","unallocated_margin_seconds","unchanged_lock_deadline_seconds","final_inventory_pacing_seconds","additional_early_source_wait_allowance_seconds","additional_serial_PDH_maximum_sample_budget_seconds"):
            self.assertEqual(before[key],after[key])
        self.assertEqual(after["additional_early_source_wait_allowance_seconds"],11)
    def test_cost_protection_600_and_wrong_diagnostic_allowance_still_reject(self):
        new=m.model_projection(original_model(),RAW["model"],scope)
        required={"a.exe":dict(path="a.exe",bytes=300*1048576,sha256="0"*64),"a.rs":dict(path="a.rs",bytes=1024,sha256="1"*64)}
        with self.assertRaises(ValueError):new(required,167)
        with self.assertRaises(ValueError):new(required,167,PDH_seconds=0)
    def test_changed_model_source_rejected_no_unqualified_cost_projection(self):
        with self.assertRaises(ValueError):m.model_projection(original_model(),RAW["model"]+b"\n",scope)
    def test_cleanup_not_called_by_pressure_and_no_new_guard_queries(self):
        obj,calls,sleeps,resources=checkpoint(cpu=95.)
        resources.close=lambda:self.fail("unexpected cleanup")
        with self.assertRaises(ValueError):obj()
        self.assertEqual(len(resources.samples),1);self.assertEqual(sleeps,[]);self.assertEqual(calls,[1])
    def test_real_acquisition_wrapper_preserved_and_only_outside_cooling_removed(self):
        class Locks:
            def __init__(self,root,checkpoint,resources,*args,**kwargs):
                self.checkpoint=checkpoint;self.saturation_checkpoint=NS(saturation_seen=False)
                self.open_pressure=P(checkpoint,resources);self.api=NS(pacer=NS(checkpoint=self.open_pressure))
                self.phase_pacer=self.api.pacer;self.phase_checkpoint=self.open_pressure
                self.original_open_checkpoint=self.open_pressure
                self.saturation_checkpoint.checkpoint=self.open_pressure
            def acquire(self):self.checkpoint();return "original_acquire"
            def summary(self):return {}
        old=NS(InputLocks=Locks,EarlySourceCheckpoint=E,PressureCheckpoint=P)
        with patch.object(acquisition.original,"load",return_value=old):
            qualified=acquisition.load(None,14,C)
        new=m.connect_api(qualified,RAW["pressure"],RAW["early"],acquisition_raw=RAW["acquisition"])
        resources=owner(20.);calls=[];sleeps=[]
        early=new.EarlySourceCheckpoint(lambda:calls.append(1),resources,sleep=lambda n:sleeps.append(n))
        held=new.InputLocks("root",early,resources)
        self.assertEqual(held.acquire(),"original_acquire");self.assertEqual(early.acquisition_checks,1)
        self.assertFalse(early.acquiring);resources.samples[:]=[dict(system_cpu_percent=90.)]
        with self.assertRaisesRegex(ValueError,"STOP_NATIVE_SOURCE_PRESSURE_NO_COOLING"):early()
        self.assertEqual(sleeps,[]);self.assertEqual(calls,[1,1])
        self.assertTrue(early.summary()["acquisition_warning_checkpoint_stop"]["original_acquisition_code_and_one_way_latch_retained"])
        self.assertFalse(early.summary()["acquisition_warning_checkpoint_stop"]["original_outside_acquisition_cooling_retained"])
    def test_mismatched_pressure_alias_is_rejected_not_silently_rebased(self):
        class Locks:
            def __init__(self):
                self.open_pressure=P(lambda:None,owner(20.));self.api=NS(pacer=NS(checkpoint=self.open_pressure))
                self.phase_pacer=self.api.pacer;self.phase_checkpoint=object()
                self.original_open_checkpoint=self.open_pressure;self.saturation_checkpoint=NS(checkpoint=self.open_pressure)
        old=NS(InputLocks=Locks,PressureCheckpoint=P,EarlySourceCheckpoint=E)
        new=m.connect_api(old,RAW["pressure"],RAW["early"])
        with self.assertRaisesRegex(ValueError,"ALL_ORIGINAL_PRESSURE_ALIAS_IDENTITIES"):new.InputLocks()

if __name__=="__main__":unittest.main()
