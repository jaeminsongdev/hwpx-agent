"""bounded handle lifetime 계약. native sharing은 별도 실제 probe로 확인한다."""
import copy
import io
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import locked_runtime_inputs as l


class FakeNative:
    def __init__(self):
        self.handles={};self.ids={};self.counter=0;self.fail_name=None;self.bad=None;self.drift=False;self.close_fail=False
        self.now=0.0;self.pacer=l.OpenPacer(lambda:None,clock=lambda:self.now,sleeper=lambda delay:setattr(self,'now',self.now+delay))
    def open(self,path,directory):
        if path.name==self.fail_name:raise ValueError('MOCK_OPEN_FAILURE')
        self.counter+=1;key=str(path);self.ids.setdefault(key,len(self.ids)+1)
        self.handles[self.counter]=dict(identity=[1,self.ids[key]],size=1,directory=directory,reparse=False,inheritable=False)
        if not directory and self.bad:self.handles[self.counter][self.bad]=True if self.bad!='size' else 2
        if self.drift and self.counter>len(self.ids):self.handles[self.counter]['identity']=[2,99]
        return self.counter
    def inspect(self,handle):return copy.deepcopy(self.handles[handle])
    def stream_handle(self,stream):return stream.native_handle
    def close(self,handle):
        if self.close_fail:return False
        del self.handles[handle];return True


class LockTests(unittest.TestCase):
    def setUp(self):
        self.pin=dict(path='tools/p09/mock.py',bytes=1,sha256='a'*64);self.api=FakeNative();self.checkpoints=[]
        self.lock=l.InputLocks(l.ROOT,lambda:self.checkpoints.append(True),self.api)
    def acquire(self):return self.lock.acquire({self.pin['path']:self.pin})

    def test_exact_pin_copied_without_mutating_input(self):
        rows={self.pin['path']:self.pin};copy_rows=l.input_pins(rows);copy_rows[self.pin['path']]['sha256']='b'*64
        self.assertEqual(self.pin['sha256'],'a'*64)
    def test_paths_absolute_traversal_ADS_alias_rejected(self):
        for name in ('/a.py','../a.py','tools/../a.py','C:/a.py','tools\\a.py','tools/a.py:stream','tools/a.py.','tools/a.py '):
            with self.assertRaises(ValueError):l.input_pins({name:dict(self.pin,path=name)})
    def test_invalid_pin_type_length_or_digest_rejected(self):
        for values in (dict(bytes=True),dict(bytes=0),dict(bytes=512*1024*1024+1),dict(sha256='A'*64),dict(path='other.py')):
            with self.assertRaises(ValueError):l.input_pins({self.pin['path']:dict(self.pin,**values)})
    def test_handle_bound_rejected_before_native_open(self):
        with patch.object(l,'MAX_HANDLES',1):
            with self.assertRaises(ValueError):self.acquire()
        self.assertEqual(self.api.counter,0)
    def test_input_count_bound_rejected(self):
        with patch.object(l,'MAX_INPUTS',1):
            with self.assertRaises(ValueError):l.input_pins(dict(a=dict(self.pin,path='a'),b=dict(self.pin,path='b')))
    def test_all_ancestor_and_file_handles_retained(self):
        self.acquire();self.assertEqual(len(self.lock.owned),4);self.assertFalse(self.lock.closed)
        self.assertTrue(self.checkpoints);self.assertTrue(self.lock.close());self.assertEqual(self.api.handles,{})
    def test_open_failure_releases_previous_handles(self):
        self.api.fail_name='mock.py'
        with self.assertRaises(ValueError):self.acquire()
        self.assertEqual(self.api.handles,{});self.assertTrue(self.lock.closed)
    def test_reparse_or_inheritable_handle_rejected(self):
        for key in ('reparse','inheritable'):
            self.setUp();self.api.bad=key
            with self.assertRaises(ValueError):self.acquire()
            self.assertEqual(self.api.handles,{})
    def test_file_size_mismatch_rejected(self):
        self.api.bad='size'
        with self.assertRaises(ValueError):self.acquire()
        self.assertEqual(self.api.handles,{})
    def test_second_acquisition_rejected(self):
        self.acquire()
        with self.assertRaises(ValueError):self.acquire()
        self.lock.close()
    def test_deadline_guard_prevents_more_native_operations(self):
        self.lock.started-=601
        with self.assertRaisesRegex(ValueError,'DEADLINE_EXCEEDED'):self.acquire()
        self.assertEqual(self.api.counter,0)
    def test_final_held_identity_verified_without_reopening_paths(self):
        self.acquire();result=self.lock.verify_held_identities();self.assertEqual(result['regular_file_count'],1)
        self.assertEqual(result['directory_count'],3);self.assertEqual(self.api.counter,4);self.lock.close()
    def test_byte_stream_pathname_replacement_rejected(self):
        self.acquire();self.api.handles[100]=dict(self.api.handles[4],identity=[2,99])
        stream=SimpleNamespace(native_handle=100)
        with self.assertRaisesRegex(ValueError,'BYTE_STREAM_IDENTITY_DRIFT'):
            self.lock.verify_stream(l.ROOT/self.pin['path'],stream)
        self.api.close(100);self.lock.close();self.assertEqual(self.api.handles,{})
    def test_held_identity_change_rejected(self):
        self.acquire();self.api.handles[1]['identity']=[2,99]
        with self.assertRaisesRegex(ValueError,'HELD_IDENTITY_DRIFT'):self.lock.verify_held_identities()
        self.lock.close()
    def test_close_failure_is_not_cleanup_success(self):
        self.acquire();self.api.close_fail=True;self.assertFalse(self.lock.close())
        self.assertFalse(self.lock.summary()['input_lock_cleanup_confirmed']);self.assertEqual(len(self.lock.owned),4)
        self.api.close_fail=False;self.assertTrue(self.lock.close())
    def test_close_idempotent_and_no_mutation_or_scope_reduction_claim(self):
        self.acquire();self.lock.close();self.assertTrue(self.lock.close())
        out=self.lock.summary();self.assertEqual(out['input_lock_handles_opened'],out['input_lock_handles_closed'])
        self.assertFalse(out['file_write_or_delete_operation_executed']);self.assertFalse(out['input_scope_reduced'])

    def test_open_pacer_cannot_accumulate_multiple_open_credits(self):
        now=[0.0];checks=[]
        pacer=l.OpenPacer(lambda:checks.append(True),clock=lambda:now[0],sleeper=lambda delay:now.__setitem__(0,now[0]+delay))
        pacer.reserve();pacer.reserve();self.assertEqual(now[0],1/32)
        now[0]+=100;pacer.reserve();before=now[0];pacer.reserve();self.assertEqual(now[0]-before,1/32)
        self.assertEqual(pacer.opens,4);self.assertTrue(checks)

    def test_open_pacer_invalid_rate_rejected(self):
        for rate in (0,33,True,1.0):
            with self.assertRaises(ValueError):l.OpenPacer(lambda:None,rate=rate)

    def test_open_pacing_does_not_disable_resource_guard(self):
        def stopped():raise ValueError('MOCK_CPU_STOP')
        pacer=l.OpenPacer(stopped)
        with self.assertRaisesRegex(ValueError,'MOCK_CPU_STOP'):pacer.reserve()
        self.assertEqual(pacer.opens,0)

    def test_two_stream_passes_confirm_identity_without_extra_path_open(self):
        self.acquire();stream=SimpleNamespace(native_handle=4);path=l.ROOT/self.pin['path']
        self.lock.verify_stream(path,stream)
        with self.assertRaises(ValueError):self.lock.verify_two_byte_passes({self.pin['path']:self.pin})
        self.lock.verify_stream(path,stream)
        result=self.lock.verify_two_byte_passes({self.pin['path']:self.pin});self.assertEqual(result['verified_byte_streams'],2)
        self.assertEqual(self.api.counter,4);self.lock.close()

    def test_hash_reader_uses_same_stream_and_shared_open_pacer(self):
        self.acquire();reader=SimpleNamespace(_source=lambda name:l.ROOT/name)
        streams=[]
        def opened(path,mode):
            stream=io.BytesIO(b'x');stream.native_handle=4;streams.append(stream);return stream
        with patch.object(Path,'open',opened),self.lock.reader_sources(reader):
            with reader._source(self.pin['path']).open('rb') as stream:self.assertEqual(stream.read(),b'x')
        self.assertTrue(streams[0].closed);self.assertEqual(self.api.pacer.opens,1)
        self.assertEqual(self.lock.stream_identity_checks,1);self.assertEqual(self.api.counter,4);self.lock.close()

    def test_reader_source_adapter_restored_after_exception(self):
        self.acquire();original=lambda name:l.ROOT/name;reader=SimpleNamespace(_source=original)
        with self.assertRaisesRegex(RuntimeError,'MOCK_READ_FAILURE'):
            with self.lock.reader_sources(reader):raise RuntimeError('MOCK_READ_FAILURE')
        self.assertIs(reader._source,original);self.lock.close()

    def test_stream_open_does_not_bypass_resource_guard(self):
        self.acquire();reader=SimpleNamespace(_source=lambda name:l.ROOT/name)
        def stopped():raise ValueError('MOCK_RESOURCE_STOP')
        self.lock.checkpoint=stopped
        with patch.object(Path,'open',side_effect=AssertionError('NO_OPEN')),self.lock.reader_sources(reader):
            with self.assertRaisesRegex(ValueError,'MOCK_RESOURCE_STOP'):
                with reader._source(self.pin['path']).open('rb'):pass
        self.lock.close()

    def test_entire_scope_open_budget_preserves_two_byte_passes(self):
        budget=l.open_budget(1467,306)
        self.assertEqual(budget['before_source_scope_open_requests'],8253)
        self.assertEqual(budget['optimized_source_scope_open_requests'],4707)
        self.assertEqual(budget['unchanged_byte_read_opens'],2934)
        self.assertEqual(budget['redundant_pathname_open_requests_removed'],3546)
        self.assertTrue(budget['model_not_measured_CPU_RAM_or_wall_time_improvement'])


if __name__=='__main__':unittest.main()
