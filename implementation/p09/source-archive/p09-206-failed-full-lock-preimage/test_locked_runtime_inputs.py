"""bounded handle lifetime 계약. native sharing은 별도 실제 probe로 확인한다."""
import copy
from pathlib import Path
import unittest
from unittest.mock import patch
import locked_runtime_inputs as l


class FakeNative:
    def __init__(self):self.handles={};self.ids={};self.counter=0;self.fail_name=None;self.bad=None;self.drift=False;self.close_fail=False
    def open(self,path,directory):
        if path.name==self.fail_name:raise ValueError('MOCK_OPEN_FAILURE')
        self.counter+=1;key=str(path);self.ids.setdefault(key,len(self.ids)+1)
        self.handles[self.counter]=dict(identity=[1,self.ids[key]],size=1,directory=directory,reparse=False,inheritable=False)
        if not directory and self.bad:self.handles[self.counter][self.bad]=True if self.bad!='size' else 2
        if self.drift and self.counter>len(self.ids):self.handles[self.counter]['identity']=[2,99]
        return self.counter
    def inspect(self,handle):return copy.deepcopy(self.handles[handle])
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
    def test_final_held_and_pathname_identity_verified(self):
        self.acquire();result=self.lock.verify_identities();self.assertEqual(result['regular_file_count'],1)
        self.assertEqual(result['directory_count'],3);self.assertEqual(len(self.api.handles),4);self.lock.close()
    def test_pathname_replacement_rejected(self):
        self.acquire();self.api.drift=True
        with self.assertRaisesRegex(ValueError,'CURRENT_PATH_IDENTITY_DRIFT'):self.lock.verify_identities()
        self.lock.close();self.assertEqual(self.api.handles,{})
    def test_held_identity_change_rejected(self):
        self.acquire();self.api.handles[1]['identity']=[2,99]
        with self.assertRaisesRegex(ValueError,'HELD_IDENTITY_DRIFT'):self.lock.verify_identities()
        self.lock.close()
    def test_close_failure_is_not_cleanup_success(self):
        self.acquire();self.api.close_fail=True;self.assertFalse(self.lock.close())
        self.assertFalse(self.lock.summary()['input_lock_cleanup_confirmed']);self.assertEqual(len(self.lock.owned),4)
        self.api.close_fail=False;self.assertTrue(self.lock.close())
    def test_close_idempotent_and_no_mutation_or_scope_reduction_claim(self):
        self.acquire();self.lock.close();self.assertTrue(self.lock.close())
        out=self.lock.summary();self.assertEqual(out['input_lock_handles_opened'],out['input_lock_handles_closed'])
        self.assertFalse(out['file_write_or_delete_operation_executed']);self.assertFalse(out['input_scope_reduced'])


if __name__=='__main__':unittest.main()
