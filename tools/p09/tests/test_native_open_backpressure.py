import threading
import time
import unittest
from types import SimpleNamespace
import native_open_backpressure as d


class Clock:
    def __init__(self):self.now=0.0;self.sleeps=[]
    def sleep(self,seconds):self.sleeps.append(seconds);self.now+=seconds
    def read(self):return self.now


class NativeOpenTests(unittest.TestCase):
    def held(self,values,*,stop=None,cached=False):
        clock=Clock();resources=SimpleNamespace(lock=threading.Lock(),samples=[],hot=0)
        seq=iter(values);calls=[];closes=[]
        def checkpoint():
            calls.append(True)
            if stop:raise ValueError(stop)
            if cached and resources.samples:return
            row=dict(system_cpu_percent=next(seq),available_ram_percent=30,commit_used_percent=40)
            resources.hot,reason=d.pressure.c.decision(row,resources.hot)
            resources.samples.append(row)
            if reason:raise ValueError(reason)
        pacer=d.borrowed.locks.OpenPacer(checkpoint,clock=clock.read,sleeper=clock.sleep)
        api=SimpleNamespace(pacer=pacer,close=lambda handle:closes.append(handle) or True)
        held=d.PressureInputLocks(d.borrowed.locks.ROOT,checkpoint,resources,api=api,pressure_sleep=clock.sleep)
        return held,clock,resources,calls,closes

    def test_normal_load_has_no_CPU_start_gate(self):
        held,clock,_,calls,_=self.held((70,94.99))
        held.api.pacer.reserve();clock.now+=1;held.api.pacer.reserve()
        self.assertEqual(clock.sleeps,[]);self.assertEqual(len(calls),2)
        self.assertEqual(held.api.pacer.opens,2)
    def test_two_distinct_cool_windows_before_open_reservation(self):
        held,clock,_,calls,_=self.held((96,94,93))
        held.api.pacer.reserve()
        self.assertEqual(clock.sleeps,[0.5,0.5]);self.assertEqual(len(calls),3)
        self.assertEqual(held.api.pacer.opens,1);self.assertEqual(clock.now,1)
    def test_original_98_four_stop_before_any_open(self):
        held,_,resources,_,_=self.held((98,99,100,100))
        with self.assertRaisesRegex(ValueError,'STOP_SUSTAINED_SYSTEM_CPU'):held.api.pacer.reserve()
        self.assertEqual(resources.hot,4);self.assertEqual(held.api.pacer.opens,0)
    def test_pause_remains_bounded(self):
        held,clock,_,_,_=self.held((95,)*9)
        with self.assertRaisesRegex(ValueError,'STOP_READ_PRESSURE_NOT_COOLING'):held.api.pacer.reserve()
        self.assertEqual(clock.sleeps,[0.5]*8);self.assertEqual(held.api.pacer.opens,0)
    def test_cached_sample_is_not_a_cool_window(self):
        held,_,_,_,_=self.held((95,),cached=True)
        with self.assertRaisesRegex(ValueError,'BACKPRESSURE_ORIGINAL_SAMPLE_NOT_ADVANCED'):held.api.pacer.reserve()
        self.assertEqual(held.api.pacer.opens,0)
    def test_original_RAM_commit_IO_stops_are_not_swallowed(self):
        for reason in ('STOP_LOW_AVAILABLE_RAM','STOP_SYSTEM_COMMIT_PRESSURE','STOP_SQL_IO_SCOPE_TIME'):
            held,clock,_,_,_=self.held((),stop=reason)
            with self.assertRaisesRegex(ValueError,reason):held.api.pacer.reserve()
            self.assertEqual(clock.sleeps,[]);self.assertEqual(held.api.pacer.opens,0)
    def test_original_lock_deadline_checked_before_open(self):
        held,_,_,_,_=self.held((20,));held.started=time.monotonic()-601
        with self.assertRaisesRegex(ValueError,'DEADLINE_EXCEEDED'):held.api.pacer.reserve()
        self.assertEqual(held.api.pacer.opens,0)
    def test_cooling_or_idle_cannot_accumulate_burst_credit(self):
        held,clock,_,_,_=self.held((96,94,93,20,20,20))
        held.api.pacer.reserve();clock.now+=10;held.api.pacer.reserve();previous=clock.now
        held.api.pacer.reserve()
        self.assertAlmostEqual(clock.now-previous,1/32);self.assertEqual(held.api.pacer.rate,32)
    def test_cleanup_works_without_sampling_or_cooling_after_stop(self):
        held,clock,_,calls,closes=self.held((),stop='STOP_LOW_AVAILABLE_RAM')
        held.owned=[('one',None,1,False),('two',None,2,False)];held.opened_handles=2
        self.assertTrue(held.close());self.assertEqual(closes,[2,1]);self.assertEqual(calls,[])
        self.assertEqual(clock.sleeps,[]);self.assertEqual(held.summary()['input_lock_handles_remaining'],0)
    def test_summary_preserves_no_actual_or_freeze_claim(self):
        held,_,_,_,_=self.held((20,));row=held.summary()['native_open_backpressure']
        self.assertTrue(row['original_frame_deadline_checked_before_open'])
        self.assertTrue(row['original_hard_resource_decisions_unmodified'])
        self.assertFalse(row['measured_CPU_or_PC_freeze_improvement_claimed'])
