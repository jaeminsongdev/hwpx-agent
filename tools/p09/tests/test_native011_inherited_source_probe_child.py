"""Synthetic kernel data for inherited reads; not child or READY evidence."""
import copy
import hashlib
from types import SimpleNamespace as NS
import unittest
import native011_inherited_source_probe_child as child


class InheritedChildContracts(unittest.TestCase):
    def fixture(self):
        payload=b'model-source';pin=dict(path='tools/p09/model.py',bytes=len(payload),sha256=hashlib.sha256(payload).hexdigest())
        row=dict(handle=11,pin=pin,identity=[1,2]);flags=[True];offset=[0];closed=[]
        class Kernel:
            body=payload;wrong_identity=False
            def info(self,handle):return dict(identity=[1,3] if self.wrong_identity else [1,2],size=len(payload),
                directory=False,reparse=False,inheritable=flags[0])
            def clear_inheritance(self,handle):flags[0]=False
            def reset(self,handle):offset[0]=0
            def readinto(self,handle,buffer):
                part=self.body[offset[0]:offset[0]+len(buffer)];buffer[:len(part)]=part;offset[0]+=len(part);return len(part)
            def close(self,handle):closed.append(handle);return True
        kernel=Kernel();reader=child.SourceReader([row],kernel,lambda:None,lambda count:None)
        return reader,kernel,row,flags,closed

    def test_actual_two_reads_not_cached_and_all_child_handles_closed(self):
        reader,kernel,row,flags,closed=self.fixture();reader.admit()
        self.assertFalse(flags[0]);self.assertEqual(reader.read_pass(),[row['pin']])
        self.assertEqual(reader.read_pass(),[row['pin']]);self.assertTrue(reader.close())
        self.assertEqual(reader.physical_bytes,2*row['pin']['bytes']);self.assertEqual(closed,[11])
        self.assertFalse(reader.summary()['actual_original_worker_READY15_or_Native_qualified'])

    def test_same_pins_wrong_os_identity_rejected_before_handle_ownership(self):
        reader,kernel,row,_,closed=self.fixture();kernel.wrong_identity=True
        with self.assertRaisesRegex(ValueError,'EXACT_INHERITED_OS_ID_NOT_PIN_ONLY'):reader.admit()
        self.assertEqual(reader.claimed,[]);self.assertEqual(closed,[])

    def test_changed_bytes_in_second_read_are_detected_not_cached(self):
        reader,kernel,row,_,_=self.fixture();reader.admit();reader.read_pass();kernel.body=b'wrong-source'
        with self.assertRaisesRegex(ValueError,'FRESH_ENTIRE_SOURCE_BYTES_AND_HASH'):reader.read_pass()
        self.assertEqual(len(reader.passes),1);self.assertTrue(reader.failed);self.assertTrue(reader.close())

    def test_serialized_bool_duplicate_handle_or_path_rejected(self):
        _,_,row,_,_=self.fixture()
        for mode in ('bool','handle','path'):
            first=copy.deepcopy(row);second=copy.deepcopy(row);second['handle']=22;second['pin']['path']='tools/p09/other.py'
            if mode=='bool':first['handle']=True
            elif mode=='handle':second['handle']=first['handle']
            else:second['pin']['path']=first['pin']['path']
            with self.assertRaises(ValueError):child.rows_checked([first,second])

    def test_third_read_pass_or_read_after_close_refused(self):
        reader,_,_,_,_=self.fixture();reader.admit();reader.read_pass();reader.read_pass()
        with self.assertRaises(ValueError):reader.read_pass()
        reader.close()
        with self.assertRaises(ValueError):reader.read_pass()

    def test_failed_cleanup_cannot_resume_reading_or_become_clean(self):
        reader,kernel,_,_,_=self.fixture();reader.admit();kernel.close=lambda handle:False
        self.assertFalse(reader.close());self.assertTrue(reader.failed)
        with self.assertRaises(ValueError):reader.read_pass()
        kernel.close=lambda handle:True
        self.assertFalse(reader.close())

    def test_identity_drift_after_admission_rejected_before_new_byte_read(self):
        reader,kernel,_,_,_=self.fixture();reader.admit();kernel.wrong_identity=True
        with self.assertRaisesRegex(ValueError,'FRESH_PRE_READ_OS_IDENTITY'):reader.read_pass()
        self.assertEqual(reader.physical_bytes,0);self.assertTrue(reader.close())

    def test_byte_pacer_has_no_idle_burst_credit(self):
        stamp=[1.0];waits=[]
        def sleep(span):waits.append(span);stamp[0]+=span
        pacer=child.BytePacer(lambda:None,clock=lambda:stamp[0],sleep=sleep)
        pacer.reserve(1000);first=sum(waits);stamp[0]+=100;waits.clear();pacer.reserve(1000)
        self.assertAlmostEqual(sum(waits),first)
        self.assertEqual(pacer.reserved_bytes,2000)
