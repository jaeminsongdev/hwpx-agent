import copy
import io
from contextlib import contextmanager
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import runtime_envelope_frame_connection_v1 as m
import runtime_input_frame as original
import owned_source_read_pressure as byte_policy
from test_runtime_envelope_scope_binding_v1 import fixture

class Held:
    def __init__(self):self.open=False;self.active_readers=set();self.counts={};self.calls=[]
    def acquire(self,rows):self.rows=rows;self.open=True;self.calls.append("acquire")
    def check(self):
        if not self.open:raise ValueError("ORIGINAL_HELD_CLOSED")
    @contextmanager
    def reader_sources(self,reader):
        self.check();self.active_readers.add(id(reader))
        try:yield
        finally:self.active_readers.remove(id(reader))
    def verify_two_byte_passes(self,inputs):self.calls.append("verify_two")
    def verify_held_identities(self):self.calls.append("identities");return dict(held_identity_checks_complete=True)
    def close(self):self.calls.append("close");self.open=False;return True
    def summary(self):return dict(input_lock_cleanup_confirmed=not self.open)

def setup():
    binding,semantic,p,raw,encoded=fixture();data={n:b"ordinary" for n in p.physical_pins}
    data[binding.manifest_pin["path"]]=b"manifest"
    for name in binding.physical:data[name]=encoded
    class Source:
        def __init__(self,name):self.name=name
        def open(self,mode):
            if mode!="rb":raise ValueError("ORIGINAL_READ_MODE")
            return io.BytesIO(data[self.name])
    class Reader(byte_policy.WeightedReader):
        def _source(self,name):return Source(name)
        def diagnostics(self):return dict(read_passes=self.read_passes,bytes_read=self.bytes_read)
    held=Held();Frame=m.frame_type(original.Frame,binding)
    frame=Frame(original.Registry(),semantic,lambda:None,held=held)
    made=[]
    def factory(guard):
        reader=Reader(Path.cwd(),guard);made.append(reader);return reader
    return frame,held,factory,made,binding,semantic

class Tests(unittest.TestCase):
    def test_actual_original_frame_two_ordered_methods_factory_called_once_each(self):
        frame,held,factory,made,binding,semantic=setup();frame.acquire()
        before=frame.read_boundary(factory,lambda:None);after=frame.read_boundary(factory,lambda:None)
        self.assertEqual(before,after);self.assertEqual(frame.original_boundary_factories,2)
        self.assertEqual(len(made),2);self.assertIs(frame.readers[0],made[0]);self.assertIs(frame.readers[1],made[1])
        self.assertEqual(frame.decoder_budget.completed,2)
        self.assertEqual(dict(frame.semantic_inputs),semantic);self.assertNotEqual(set(frame.inputs),set(semantic))
        frame.close();self.assertEqual(frame.summary()["frame_state"],"CLOSED")
    def test_original_commit_still_demands_real_owned_cleanup_not_synthesized(self):
        frame,held,factory,made,binding,semantic=setup();frame.acquire()
        frame.read_boundary(factory,lambda:None);frame.read_boundary(factory,lambda:None)
        with self.assertRaisesRegex(ValueError,"ORIGINAL_JOB_CLEANUP_BEFORE_FRAME_RELEASE"):
            frame.commit(dict(cleanup_confirmed=False,owned_tree_empty=True))
        self.assertNotIn("verify_two",held.calls);frame.close()
    def test_original_wrong_boundary_order_and_incomplete_commit_rejected(self):
        frame,held,factory,made,binding,semantic=setup();frame.acquire()
        with self.assertRaisesRegex(ValueError,"COMPLETE_TWO_BYTE_BOUNDARIES"):frame.commit({})
        frame.read_boundary(factory,lambda:None);frame.read_boundary(factory,lambda:None)
        with self.assertRaisesRegex(ValueError,"EXACT_TWO_ORDERED_BOUNDARIES"):frame.read_boundary(factory,lambda:None)
        frame.close()
    def test_adopt_retains_same_reader_pacer_and_all_fields_no_second_constructor(self):
        frame,held,factory,made,binding,semantic=setup();reader=factory(lambda:None);fields=dict(vars(reader));pacer=reader.pacer
        adopted=m.adopt_fresh_reader(reader,frame.explicit_projection,frame.decoder_budget)
        self.assertIs(adopted,reader);self.assertIs(reader.pacer,pacer)
        for key,value in fields.items():self.assertIs(vars(reader)[key],value)
        reader.read_passes=1
        with self.assertRaisesRegex(ValueError,"FRESH_FACTORY_READER_ONLY"):m.adopt_fresh_reader(reader,frame.explicit_projection,frame.decoder_budget)
    def test_guard_stop_preserved_and_original_reader_binding_cleanup_attempted(self):
        frame,held,factory,made,binding,semantic=setup();frame.acquire();error=ValueError("ORIGINAL_STOP")
        def stop():raise error
        with self.assertRaises(ValueError) as caught:frame.read_boundary(factory,stop)
        self.assertIs(caught.exception,error);self.assertFalse(held.active_readers);self.assertFalse(frame.reading)
        self.assertTrue(frame.close())
    def test_metadata_or_worker_access_policy_not_claimed_connected(self):
        frame,held,factory,made,binding,semantic=setup()
        self.assertFalse(frame.summary()["metadata_and_worker_raw_live_access_policy_connected"])
        self.assertFalse(frame.summary()["whole_product_connection_qualified"])

if __name__=="__main__":unittest.main()
