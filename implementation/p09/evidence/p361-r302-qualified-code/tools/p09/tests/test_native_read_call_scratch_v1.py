import ctypes
import sys
import threading
import unittest
from pathlib import Path
from types import SimpleNamespace as NS
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import native_read_call_scratch_v1 as m

class Fn:
    def __init__(self,call):self.call=call
    def __call__(self,*args):return self.call(*args)

class Fake:
    def __init__(self):
        self.read_ids=[];self.seek_ids=[];self.before=[];self.payload=b"abc";self.fail=False;self.hook=None
        self.ReadFile=Fn(self.read);self.SetFilePointerEx=Fn(self.seek)
    def read(self,h,buf,size,pointer,overlap):
        self.read_ids.append((id(pointer),id(pointer._obj)));self.before.append(pointer._obj.value)
        if self.hook:self.hook()
        if self.fail:return False
        count=min(size,len(self.payload))
        for i,b in enumerate(self.payload[:count]):buf[i]=b
        pointer._obj.value=count
        return True
    def seek(self,h,offset,pointer,whence):
        self.seek_ids.append((id(pointer),id(pointer._obj)))
        if self.fail:return False
        pointer._obj.value=0;return True

class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw=(Path(__file__).resolve().parents[3]/m.ORIGINAL_PIN["path"]).read_bytes()
        cls.Type,cls.proof=m.native_read_type(cls.raw)
    def setUp(self):
        self.k=Fake();self.api=self.Type(NS(k=self.k))
    def test_read_count_and_pointer_reused_but_bytes_fresh_and_zero_reset(self):
        data=bytearray(8);self.assertEqual(self.api.readinto(1,data),3)
        self.assertEqual(data[:3],b"abc")
        self.k.payload=b"";self.assertEqual(self.api.readinto(1,data),0)
        self.k.payload=b"xy";self.assertEqual(self.api.readinto(1,data),2)
        self.assertEqual(data[:2],b"xy")
        self.assertEqual(len(set(self.k.read_ids)),1);self.assertEqual(self.k.before,[0,0,0])
        self.assertFalse(self.api._busy)
    def test_seek_scratch_and_pointer_reused_with_reset(self):
        self.assertEqual(self.api.reset(1),0);self.api._seek_result.value=7
        self.assertEqual(self.api.reset(1),0);self.assertEqual(len(set(self.k.seek_ids)),1)
    def test_original_bounds_and_writable_buffer_errors_preserved(self):
        for buffer in (bytearray(),bytearray(65537),b"abc"):
            with self.assertRaises((ValueError,TypeError)):self.api.readinto(1,buffer)
            self.assertFalse(self.api._busy)
        self.assertEqual(len(self.k.read_ids),0)
    def test_OS_failures_propagate_and_release_scratch(self):
        self.k.fail=True
        for call in (lambda:self.api.reset(1),lambda:self.api.readinto(1,bytearray(3))):
            with self.assertRaises(OSError):call()
            self.assertFalse(self.api._busy)
        self.k.fail=False;self.assertEqual(self.api.readinto(1,bytearray(3)),3)
    def test_other_owner_and_reentry_rejected_before_second_OS_call(self):
        results=[]
        def other():
            try:self.api.reset(1)
            except ValueError:results.append("REJECTED")
        t=threading.Thread(target=other);t.start();t.join(1)
        self.assertFalse(t.is_alive());self.assertEqual(results,["REJECTED"]);self.assertFalse(self.k.seek_ids)
        self.k.hook=lambda:self.api.readinto(1,bytearray(3))
        with self.assertRaises(ValueError):self.api.readinto(1,bytearray(3))
        self.assertEqual(len(self.k.read_ids),1);self.assertFalse(self.api._busy)
    def test_exact_source_AST_original_calls_and_no_product_claim(self):
        with self.assertRaises(ValueError):m.project(self.raw+b" ")
        for value in self.proof["original_methods"].values():
            self.assertTrue(value["original_AST_restored_exactly"])
            self.assertEqual(value["original_guard_error_identity_and_fresh_buffer_statements_removed"],0)
        self.assertEqual(self.proof["original_chunk_ceiling"],65536)
        self.assertFalse(self.proof["byte_hash_JSON_identity_cache"])
        self.assertFalse(self.proof["current149_runtime_connection"])
        self.assertFalse(self.proof["PC_freeze_resolved"])

if __name__=="__main__":unittest.main()
