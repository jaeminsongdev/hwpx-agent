"""Fake Native/owner regressions; no live Native frame or product child."""
import json
from pathlib import Path
import sys
import threading
from types import SimpleNamespace as NS
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
sys.path.insert(0,str(Path(__file__).resolve().parent))
import current_queue_acquisition_checkpoint as b
import accept_case112_current_epoch as a
from test_current_stored_native_bridge import Reader,PacerNative


class AcquisitionCheckpointContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.api=b.load(Reader(),14,a.c)
    def held(self,base=None,pacer_sleep_hook=None):
        owner=NS(lock=threading.Lock(),samples=[dict(system_cpu_percent=20)])
        native=PacerNative();calls=[]
        if pacer_sleep_hook:
            original_sleep=native.pacer.sleeper
            def sleep(delay):original_sleep(delay);pacer_sleep_hook(owner)
            native.pacer.sleeper=sleep
        checkpoint=self.api.EarlySourceCheckpoint(base or (lambda:calls.append(True)),owner)
        native.pacer.checkpoint=checkpoint
        held=self.api.InputLocks(a.c.ROOT,checkpoint,owner,NS(phase='metadata_hash'),api=native)
        return held,native,owner,calls
    def rows(self):return {'tools/p09/mock.py':dict(path='tools/p09/mock.py',bytes=1,sha256='a'*64)}
    def test_normal_original_acquire_identity_pacer_credit_rate_cleanup(self):
        held,native,owner,calls=self.held();held.acquire(self.rows())
        self.assertEqual(native.rates,[14]*4);self.assertEqual(native.pacer.rate,20)
        self.assertFalse(held.checkpoint.acquiring);self.assertFalse(held.checkpoint.acquisition_latched)
        self.assertTrue(calls);self.assertTrue(held.close());self.assertEqual(native.handles,{})
    def test_warning_during_original_checkpoint_stops_without_cooling_before_open(self):
        held,native,owner,calls=self.held()
        count=0
        def base():
            nonlocal count
            count+=1
            if count>=4:owner.samples[:]=[dict(system_cpu_percent=94.15)]
        held.checkpoint.base=base
        held.checkpoint.sleep=lambda _:self.fail('No doomed acquisition cooling')
        with self.assertRaisesRegex(ValueError,'STOP_NATIVE_OPEN_AFTER_HOST_SATURATION'):
            held.acquire(self.rows())
        self.assertTrue(held.checkpoint.acquisition_latched)
        self.assertEqual(held.checkpoint.acquisition_warning_stops,1)
        self.assertEqual(held.checkpoint.windows,0)
        self.assertTrue(held.saturation_checkpoint.saturation_seen)
        self.assertFalse(held.checkpoint.acquiring);self.assertTrue(held.closed)
        self.assertEqual(native.handles,{})
    def test_warning_on_original_pacer_wait_callback_latches_before_dispatch(self):
        held,native,owner,calls=self.held(pacer_sleep_hook=lambda owner:
            owner.samples.__setitem__(slice(None),[dict(system_cpu_percent=91)]))
        held.checkpoint.sleep=lambda _:self.fail('No acquisition cooling after reservation warning')
        with self.assertRaisesRegex(ValueError,'STOP_NATIVE_OPEN_AFTER_HOST_SATURATION'):
            held.acquire(self.rows())
        self.assertEqual(len(native.rates),1);self.assertEqual(native.handles,{})
        self.assertEqual(native.pacer.rate,20);self.assertEqual(held.checkpoint.windows,0)
    def test_latched_acquisition_never_resamples_or_resumes(self):
        held,native,owner,calls=self.held();early=held.checkpoint
        early.acquiring=True;owner.samples[:]=[dict(system_cpu_percent=90)]
        with self.assertRaises(ValueError):early()
        owner.samples[:]=[dict(system_cpu_percent=1)];before=len(calls)
        with self.assertRaises(ValueError):early()
        self.assertEqual(len(calls),before);self.assertEqual(native.counter,0)
        early.acquiring=False;self.assertTrue(held.close())
    def test_original_hard_resource_stop_before_warning_and_deadline_before_open(self):
        held,native,owner,calls=self.held();owner.samples[:]=[dict(system_cpu_percent=100)]
        def stop():raise ValueError('STOP_SYSTEM_COMMIT_PRESSURE')
        held.checkpoint.base=stop
        with self.assertRaisesRegex(ValueError,'STOP_SYSTEM_COMMIT_PRESSURE'):held.acquire(self.rows())
        self.assertEqual(native.counter,0);self.assertEqual(held.checkpoint.acquisition_warning_stops,0)
        held,native,owner,calls=self.held();held.started-=601
        with self.assertRaisesRegex(ValueError,'DEADLINE_EXCEEDED'):held.acquire(self.rows())
        self.assertEqual(native.counter,0);self.assertFalse(held.checkpoint.acquiring)
    def test_outside_acquisition_original90_two_distinct_cool_windows_retained(self):
        owner=NS(lock=threading.Lock(),samples=[dict(system_cpu_percent=90)])
        calls=[]
        def sleep(delay):
            self.assertEqual(delay,.5);owner.samples.append(dict(system_cpu_percent=20))
        early=self.api.EarlySourceCheckpoint(lambda:calls.append(True),owner,sleep=sleep)
        early();self.assertEqual(early.warning_entries,1);self.assertEqual(early.windows,2)
        self.assertEqual(len(calls),3);self.assertEqual(early.acquisition_checks,0)
    def test_original_sample_validation_and_missing_owner_not_masked(self):
        held,native,owner,calls=self.held();held.checkpoint.acquiring=True
        for value in (True,float('nan'),101):
            owner.samples[:]=[dict(system_cpu_percent=value)]
            with self.subTest(),self.assertRaisesRegex(ValueError,'CPU_INVALID'):held.checkpoint()
        held.checkpoint.acquiring=False;self.assertTrue(held.close())
    def test_failed_native_open_restores_original20_and_scope_and_cleanup(self):
        held,native,owner,calls=self.held();native.fail_name='mock.py'
        with self.assertRaisesRegex(ValueError,'MOCK_OPEN_FAILURE'):held.acquire(self.rows())
        self.assertEqual(native.pacer.rate,20);self.assertFalse(held.checkpoint.acquiring)
        self.assertEqual(native.handles,{});self.assertTrue(held.closed)


if __name__=='__main__':
    guard=a.Guard();result=None
    try:
        guard.acquire()
        result=unittest.TextTestRunner(verbosity=1).run(unittest.defaultTestLoader.loadTestsFromTestCase(AcquisitionCheckpointContracts))
        guard.check(force=True)
    finally:guard.close()
    print(json.dumps(dict(contract_count=result.testsRun if result else 0,passed=bool(result and result.wasSuccessful()),
        cleanup_confirmed=guard.cleanup,product_child_executed=False)))
    raise SystemExit(0 if result and result.wasSuccessful() and guard.cleanup else 2)
