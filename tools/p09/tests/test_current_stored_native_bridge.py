import ast
import copy
import hashlib
import json
import math
from pathlib import Path
import sys
import threading
from types import SimpleNamespace as NS
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import current_stored_native_bridge as bridge
import conservative_maintenance as c
from test_locked_runtime_inputs import FakeNative


class Reader:
    def __init__(self):self.snapshots={}
    def text(self,name):
        raw=(c.ROOT/name).read_bytes()
        self.snapshots[name]=dict(path=name,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
        return raw.decode('utf-8').replace('\r\n','\n')


class PacerNative(FakeNative):
    def __init__(self):
        super().__init__();self.rates=[]
        self.pacer.sleeper=lambda delay:setattr(self,'now',math.nextafter(self.now+delay,math.inf))
    def open(self,path,directory):
        self.pacer.reserve();self.rates.append(self.pacer.rate)
        return super().open(path,directory)


class LeanNativeContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.lean=bridge.load(Reader(),12,c)
    def held(self,base=None):
        calls=[];base=base or (lambda:calls.append(True));api=PacerNative();api.pacer.checkpoint=base
        owner=NS(lock=threading.Lock(),samples=[dict(system_cpu_percent=20)])
        early=self.lean.EarlySourceCheckpoint(base,owner)
        api.pacer.checkpoint=early
        obj=self.lean.InputLocks(c.ROOT,early,owner,NS(phase='metadata_hash'),api=api)
        return obj,api,owner,calls
    def rows(self):return {'tools/p09/mock.py':dict(path='tools/p09/mock.py',bytes=1,sha256='a'*64)}
    def test_original_sources_match_historical_or_exact_current_observation(self):
        doc=json.loads((c.ROOT/'implementation/p09/evidence/locked-r07/cases/p340-failure-111-run083.json').read_text())
        original={z['path']:z for z in doc['source_freeze']}
        self.assertTrue(all(original[z['path']]==z for z in bridge.SOURCES[:-1]))
        self.assertEqual(bridge.SOURCES[-1]['sha256'],'499dfe358b31728f0ebb1d0bc21398bdcce7dbd77d8c424a9fff8b58c252770b')
    def test_no_module_top_level_execution(self):
        result=bridge.definitions('raise AssertionError("not executed")\nclass Kept:\n    value=7\n',('Kept',),{})
        self.assertEqual(result.Kept.value,7)
    def test_missing_duplicate_import_or_dynamic_import_definition_rejected(self):
        for text in ('class Other: pass','class Kept: pass\nclass Kept: pass',
                     'class Kept:\n import os','class Kept:\n value=__import__("os")'):
            with self.subTest(text=text),self.assertRaises(ValueError):bridge.definitions(text,('Kept',),{})
    def test_source_pin_drift_rejected_before_class_loading(self):
        reader=Reader();original=reader.text
        def changed(name):
            value=original(name);reader.snapshots[name]['sha256']='a'*64;return value
        reader.text=changed
        with self.assertRaisesRegex(ValueError,'EXACT_SOURCE_PIN'):bridge.load(reader,12,c)
    def test_selected_acquisition_rate_only_and_original20_restored_without_credit_reset(self):
        held,api,_,calls=self.held();held.acquire(self.rows())
        self.assertEqual(api.rates,[12]*4);self.assertEqual(api.pacer.rate,20)
        previous=api.pacer.previous;opens=api.pacer.opens
        api.pacer.reserve();self.assertEqual(api.pacer.opens,opens+1)
        self.assertGreater(api.pacer.previous,previous)
        self.assertTrue(calls);self.assertTrue(held.close());self.assertEqual(api.handles,{})
    def test_failure_restores20_and_closes_previous_handles(self):
        held,api,_,_=self.held();api.fail_name='mock.py'
        with self.assertRaisesRegex(ValueError,'MOCK_OPEN_FAILURE'):held.acquire(self.rows())
        self.assertEqual(api.pacer.rate,20);self.assertTrue(held.closed);self.assertEqual(api.handles,{})
    def test_deadline_and_original_resource_stop_precede_any_open(self):
        held,api,_,_=self.held();held.started-=601
        with self.assertRaisesRegex(ValueError,'DEADLINE_EXCEEDED'):held.acquire(self.rows())
        self.assertEqual(api.counter,0)
        def stop():raise ValueError('STOP_LOW_AVAILABLE_RAM')
        held,api,_,_=self.held(stop)
        with self.assertRaisesRegex(ValueError,'STOP_LOW_AVAILABLE_RAM'):held.acquire(self.rows())
        self.assertEqual(api.counter,0)
    def test_previous_early_source_warning_latches_before_next_checkpoint_or_open(self):
        held,api,_,calls=self.held();held.checkpoint.warning_entries+=1
        before=len(calls)
        with self.assertRaisesRegex(ValueError,'STOP_NATIVE_OPEN_AFTER_HOST_SATURATION'):held.acquire(self.rows())
        self.assertEqual(api.counter,0);self.assertTrue(held.saturation_checkpoint.saturation_seen)
        # take performs its original held.check before entering the Native pacer.
        self.assertGreaterEqual(len(calls),before)
    def test_native_pressure95_and_two_distinct_existing_samples_retained(self):
        owner=NS(lock=threading.Lock(),samples=[dict(system_cpu_percent=95)])
        calls=[]
        def sleep(delay):
            self.assertEqual(delay,.5);owner.samples.append(dict(system_cpu_percent=20))
        check=self.lean.PressureCheckpoint(lambda:calls.append(True),owner,sleep=sleep)
        check();self.assertEqual(check.warning_entries,1);self.assertEqual(check.pause_windows,2)
        self.assertEqual(len(calls),3)
    def test_native_pressure_stale_sample_not_cooling_and_hard_stop_not_swallowed(self):
        owner=NS(lock=threading.Lock(),samples=[dict(system_cpu_percent=95)])
        check=self.lean.PressureCheckpoint(lambda:None,owner,sleep=lambda _:None)
        with self.assertRaisesRegex(ValueError,'SAMPLE_NOT_ADVANCED'):check()
        def stop():raise ValueError('STOP_SYSTEM_COMMIT_PRESSURE')
        with self.assertRaisesRegex(ValueError,'STOP_SYSTEM_COMMIT_PRESSURE'):
            self.lean.PressureCheckpoint(stop,owner)()
    def test_first_source90_warning_stops_acquisition_without_cooling_or_native_open(self):
        held,api,owner,calls=self.held();owner.samples[:]=[dict(system_cpu_percent=90)]
        held.checkpoint.sleep=lambda _:self.fail('Native acquisition must not wait for cooling before latching')
        with self.assertRaisesRegex(ValueError,'STOP_NATIVE_OPEN_AFTER_HOST_SATURATION'):
            held.take('tools/p09/mock.py',c.ROOT/'tools/p09/mock.py',False,self.rows()['tools/p09/mock.py'])
        self.assertEqual(api.counter,0);self.assertEqual(held.preflight_latches,1)
        self.assertTrue(held.saturation_checkpoint.saturation_seen)
        before=len(calls)
        with self.assertRaisesRegex(ValueError,'STOP_NATIVE_OPEN_AFTER_HOST_SATURATION'):
            held.take('tools/p09/mock.py',c.ROOT/'tools/p09/mock.py',False,self.rows()['tools/p09/mock.py'])
        self.assertEqual(len(calls),before);self.assertTrue(held.close())
    def test_hard_commit_stop_precedes_source_warning_fail_fast(self):
        def stop():raise ValueError('STOP_SYSTEM_COMMIT_PRESSURE')
        held,api,owner,_=self.held(stop);owner.samples[:]=[dict(system_cpu_percent=100)]
        with self.assertRaisesRegex(ValueError,'STOP_SYSTEM_COMMIT_PRESSURE'):
            held.take('tools/p09/mock.py',c.ROOT/'tools/p09/mock.py',False,self.rows()['tools/p09/mock.py'])
        self.assertEqual(held.preflight_latches,0);self.assertEqual(api.counter,0);self.assertTrue(held.close())
    def test_acquisition_identity_inheritance_size_and_close_failure_not_weakened(self):
        for field in ('reparse','inheritable','size'):
            held,api,_,_=self.held();api.bad=field
            with self.subTest(field=field),self.assertRaises(ValueError):held.acquire(self.rows())
            self.assertEqual(api.handles,{})
        held,api,_,_=self.held();held.acquire(self.rows());api.close_fail=True
        self.assertFalse(held.close());self.assertEqual(len(held.owned),4)
        api.close_fail=False;self.assertTrue(held.close())
    def test_rate_closed_and_exact_original_class_ast(self):
        for rate in (True,0,15,'12'):
            with self.subTest(rate=rate),self.assertRaises(ValueError):bridge.load(Reader(),rate,c)
        self.assertTrue(issubclass(self.lean.InputLocks,bridge.borrowed.BorrowedInputLocks))
        text=Reader().text(bridge.SOURCES[4]['path']);node=next(n for n in ast.parse(text).body if isinstance(n,ast.ClassDef) and n.name=='InputLocks')
        self.assertEqual(self.lean.original_phase_base.acquire.__code__.co_firstlineno,node.body[1].lineno)
    def test_all_held_final_identities_and_diagnostic_counts(self):
        held,api,_,_=self.held();held.acquire(self.rows());held.verify_held_identities()
        row=held.summary();self.assertEqual(row['native_acquisition_diagnostics']['take_completed'],4)
        self.assertEqual(row['acquisition_phase_pressure']['nominal_acquisition_density_reduction_percent'],40)
        self.assertFalse(row['historical_runner_top_level_imported']);self.assertTrue(held.close())


if __name__=='__main__':unittest.main()
