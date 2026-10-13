import hashlib
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import held_envelope_boundary_guard_v1 as m

def fixture(stop=None):
    source=m.original.source; raw=b'{"all":true}\n'; encoded=source.codec.encode(raw,lambda:None)
    pin=lambda name,data:dict(path=name,bytes=len(data),sha256=hashlib.sha256(data).hexdigest())
    logical=pin("implementation/p09/evidence/p09-361-case157-current-runtime-run001.v1.json",raw)
    physical=pin(source.PREFIX+"case157-runtime-run001.envelope.v1.json",encoded)
    desc=source.descriptor(logical,physical,next_case=158)
    p=source.Projection({logical["path"]:logical},[desc],next_case=158,checkpoint=lambda:None)
    events=[]
    def parent():events.append("original_parent_guard")
    budget=m.original.DecoderBudget(parent)
    class Base:
        def __init__(self):self.open=True;self.checkpoint=self.live
        def live(self):
            events.append("original_Frame_guard")
            if not self.open:raise stop or ValueError("ORIGINAL_NATIVE_FRAME_CLOSED")
        def _read(self,name,parse=False):
            events.append(("original_physical_read",name,parse));return physical,bytearray(encoded)
        def diagnostics(self):return {}
    New=m.boundary_reader_type(Base,p,budget)
    return New,budget,physical,parent,events

class Tests(unittest.TestCase):
    def test_success_scopes_actual_boundary_guard_and_restores_callback(self):
        New,b,p,parent,events=fixture();reader=New()
        self.assertEqual(reader._read(p["path"]),(p,None));self.assertIs(b.checkpoint,parent)
        self.assertGreater(reader.envelope_original_boundary_guard_calls,0)
        self.assertIn("original_Frame_guard",events);self.assertEqual(b.completed,1)
    def test_closed_Frame_after_physical_read_cannot_decode_success(self):
        New,b,p,parent,events=fixture();reader=New();reader.open=False
        with self.assertRaisesRegex(ValueError,"ORIGINAL_NATIVE_FRAME_CLOSED"):reader._read(p["path"])
        self.assertIs(b.checkpoint,parent);self.assertEqual(b.completed,0)
        self.assertEqual(reader.semantic_decode_counts,{})
    def test_original_Frame_exception_identity_preserved_and_callback_restored(self):
        error=OSError("ORIGINAL_LOCK_FAILURE");New,b,p,parent,events=fixture(error);reader=New();reader.open=False
        with self.assertRaises(OSError) as caught:reader._read(p["path"])
        self.assertIs(caught.exception,error);self.assertIs(b.checkpoint,parent)
    def test_two_reader_instances_use_one_budget_no_stale_boundary_callback(self):
        New,b,p,parent,events=fixture();one,two=New(),New()
        one._read(p["path"]);one.open=False;two._read(p["path"])
        self.assertIs(b.checkpoint,parent);self.assertEqual(b.completed,2)
        self.assertGreater(two.envelope_original_boundary_guard_calls,0)
    def test_ordinary_source_does_not_rebind_or_consume_decoder(self):
        New,b,p,parent,events=fixture();reader=New();reader.open=False
        reader._read("crates/current.rs",parse=True)
        self.assertIs(b.checkpoint,parent);self.assertEqual(b.attempts,0)
        self.assertEqual(reader.envelope_original_boundary_guard_calls,0)
    def test_original_parent_guard_precedes_Frame_guard(self):
        New,b,p,parent,events=fixture();reader=New();reader._read(p["path"])
        for i,item in enumerate(events):
            if item=="original_Frame_guard":self.assertEqual(events[i-1],"original_parent_guard")

if __name__=="__main__":unittest.main()
