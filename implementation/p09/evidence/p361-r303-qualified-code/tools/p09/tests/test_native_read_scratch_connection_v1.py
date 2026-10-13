import copy
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace as NS
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
sys.path.insert(0,str(Path(__file__).resolve().parent))
import native_read_scratch_connection_v1 as m
from test_native_read_call_scratch_v1 import Fake

class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw=(Path(__file__).resolve().parents[3]/m.scratch.ORIGINAL_PIN["path"]).read_bytes()
        cls.old=m.scratch.prior;cls.new,cls.proof=m.connect(cls.old,cls.raw)
    def borrower(self,api=None):
        self.k=Fake();path=Path("component.py")
        self.held=NS(acquired=True,closed=False,releasing=False,
           api=NS(k=self.k,pacer=NS(checkpoint=lambda:None)),owned=[("x",path,1,False)],
           check=lambda:None,active_readers=set())
        owner=self.new.ViewBorrower(self.held,api)
        self.held.borrower=owner
        reader=NS(_p206_input_lock_owner=self.held)
        self.held.active_readers.add(id(reader));owner.active_binding=True;owner.bound_reader=reader
        return owner,reader,path
    def test_full_native_load_locks_init_and_no_namespace_mutation(self):
        self.assertIs(self.new.load.__code__,self.old.load.__code__)
        self.assertIs(self.new.locks_type.__code__,self.old.locks_type.__code__)
        self.assertIs(self.new.ViewBorrower.__init__.__code__,self.old.ViewBorrower.__init__.__code__)
        self.assertIs(self.new.ReadView,self.old.ReadView)
        self.assertIs(self.new.model,self.old.model)
        self.assertIs(self.old.ViewBorrower.__init__.__globals__["NativeRead"],self.old.NativeRead)
    def test_real_factory_reaches_original_ReadView_fresh_two_passes(self):
        owner,reader,path=self.borrower()
        expected=[]
        for text in (b"abc",b"xy"):
            self.k.payload=text;owner.reserve(reader,path)
            with owner.open(path,"rb") as stream:
                buf=bytearray(8);n=stream.readinto(buf);expected.append(bytes(buf[:n]))
                self.assertEqual(stream.readinto(buf),3 if False else len(text))
        self.assertEqual(expected,[b"abc",b"xy"])
        info=owner.summary();self.assertTrue(info["native_call_scratch"]["actual_default_factory_bound"])
        self.assertEqual(info["direct_readinto_attempts"],4);self.assertEqual(info["shared_offset_resets"],2)
        self.assertEqual(len(set(self.k.read_ids)),1);self.assertFalse(owner.loan)
        owner.active_binding=False
        row=dict(selected_test_index=150,source_frame=dict(input_count=1,handles=dict(held_native_read_views=info)))
        m.validate_scratch(row)
    def test_old_summary_fields_retained_and_fake_API_not_promoted(self):
        owner,reader,path=self.borrower(NS())
        original=self.old.ViewBorrower.summary(owner);actual=owner.summary()
        self.assertEqual({k:actual[k] for k in original},original)
        self.assertFalse(actual["native_call_scratch"]["actual_default_factory_bound"])
        row=dict(selected_test_index=150,source_frame=dict(input_count=1,handles=dict(held_native_read_views=actual)))
        with self.assertRaises(ValueError):m.validate_scratch(row)
    def test_strict_call_counts_types_owner_and_no_extra_fields(self):
        owner,reader,path=self.borrower()
        for _ in range(2):
            owner.reserve(reader,path)
            with owner.open(path,"rb") as stream:stream.readinto(bytearray(8))
        row=dict(selected_test_index=150,source_frame=dict(input_count=1,handles=dict(held_native_read_views=owner.summary())))
        m.validate_scratch(row)
        for key,value in (("actual_default_factory_bound",False),("original_actual_read_calls",True),
                          ("source","other"),("scratch_active",True)):
            bad=copy.deepcopy(row);bad["source_frame"]["handles"]["held_native_read_views"]["native_call_scratch"][key]=value
            with self.assertRaises(ValueError):m.validate_scratch(bad)
        bad=copy.deepcopy(row);bad["source_frame"]["handles"]["held_native_read_views"]["native_call_scratch"]["extra"]=1
        with self.assertRaises(ValueError):m.validate_scratch(bad)
    def test_recorded149_not_relabelled_and_original_validator_first(self):
        row=dict(selected_test_index=149);before=copy.deepcopy(row);calls=[]
        connected=m.diagnostic(NS(validate=lambda r:calls.append(r) or dict(original=True)))
        self.assertTrue(connected.validate(row)["historical_scratch_not_claimed"])
        self.assertEqual(calls,[row]);self.assertEqual(row,before)
        def reject(r):raise ValueError("ORIGINAL")
        with self.assertRaisesRegex(ValueError,"ORIGINAL"):m.diagnostic(NS(validate=reject)).validate(row)
    def test_bounds_and_OS_error_still_propagate_through_ReadView(self):
        owner,reader,path=self.borrower();owner.reserve(reader,path)
        with owner.open(path,"rb") as stream:
            with self.assertRaises(ValueError):stream.readinto(bytearray(65537))
            self.k.fail=True
            with self.assertRaises(OSError):stream.readinto(bytearray(3))
        self.assertFalse(owner.loan);self.assertEqual(owner.summary()["logical_views_remaining"],0)

if __name__=="__main__":unittest.main()
