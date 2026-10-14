import hashlib
import json
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
sys.path.insert(0,str(Path(__file__).resolve().parent))
import prepared_checkpoint_transport_v1 as m
import test_prepared_scope_handoff_v1 as fixture

def pin(path,raw):return dict(path=path,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
class Reader:
    def __init__(self,path,raw):self.path=path;self.raw=raw;self.snapshots={};self.reads=0
    def checkpoint(self):pass
    def _read(self,path,parse=False):
        assert path==self.path and parse is True
        self.reads+=1;return pin(path,self.raw),bytearray(self.raw)
    def _bind(self,path,value):
        if path in self.snapshots:assert self.snapshots[path]==value
        self.snapshots[path]=dict(value)
class Tests(unittest.TestCase):
    def setUp(self):
        self.f=fixture.Tests();self.f.setUp()
        self.raw=json.dumps(self.f.row,ensure_ascii=True,indent=2).encode("utf-8")
        self.encoded=m.codec.encode(self.raw,lambda:None)
        self.semantic=pin("raw-checkpoint",self.raw);self.physical=pin("carrier",self.encoded)
    def load(self,q=None,**values):
        return m.load(q or Reader("carrier",self.encoded),values.get("semantic",self.semantic),
            values.get("physical",self.physical),self.f.binding,**self.f.args)
    def test_entire_scope_and_exact_original_bytes_retained(self):
        scope,_,proof=self.load()
        self.assertEqual(scope,{**self.f.scope,"carrier":self.physical})
        self.assertTrue(proof["exact_original_checkpoint_bytes_decoded"])
        self.assertFalse(proof["GO_authorized"])
    def test_reader_ledger_records_only_actual_physical_bytes(self):
        q=Reader("carrier",self.encoded);_,_,proof=self.load(q)
        self.assertEqual(q.snapshots,{"carrier":self.physical})
        self.assertFalse(proof["semantic_original_claimed_as_live_raw_Native_input"])
        self.assertNotIn("checkpoint_original_added_to_required_scope",proof)
    def test_wrong_original_hash_rejected(self):
        with self.assertRaises(ValueError):self.load(semantic=dict(self.semantic,sha256="b"*64))
    def test_wrong_original_size_rejected(self):
        with self.assertRaises(ValueError):self.load(semantic=dict(self.semantic,bytes=self.semantic["bytes"]+1))
    def test_wrong_physical_pin_rejected(self):
        with self.assertRaises(ValueError):self.load(physical=dict(self.physical,sha256="b"*64))
    def test_same_path_is_not_implicit_alias(self):
        with self.assertRaises(ValueError):self.load(semantic=dict(self.semantic,path="carrier"))
    def test_expansion_over_checkpoint_cap_rejected_before_read(self):
        q=Reader("carrier",self.encoded)
        with self.assertRaises(ValueError):self.load(q,semantic=dict(self.semantic,bytes=m.original.MAX_CHECKPOINT_BYTES+1))
        self.assertEqual(q.reads,0)
    def test_truncated_payload_rejected(self):
        row=json.loads(self.encoded);row["payload"]=row["payload"][:-8]
        raw=json.dumps(row).encode("utf-8")
        with self.assertRaises(ValueError):self.load(Reader("carrier",raw),physical=pin("carrier",raw))
    def test_duplicate_carrier_key_rejected(self):
        raw=self.encoded.rstrip()[:-1]+b',"original_bytes":1}'
        with self.assertRaises(ValueError):self.load(Reader("carrier",raw),physical=pin("carrier",raw))
    def test_decoded_go_claim_still_rejected_by_original_checker(self):
        self.f.row["GO_authorized"]=True
        raw=json.dumps(self.f.row).encode("utf-8");encoded=m.codec.encode(raw,lambda:None)
        with self.assertRaises(ValueError):self.load(Reader("carrier",encoded),semantic=pin("raw-checkpoint",raw),physical=pin("carrier",encoded))
    def test_original_resource_stop_identity_preserved(self):
        q=Reader("carrier",self.encoded);error=ValueError("ORIGINAL_RESOURCE_STOP")
        def stop():raise error
        q.checkpoint=stop
        with self.assertRaises(ValueError) as caught:self.load(q)
        self.assertIs(caught.exception,error)
    def test_no_file_or_json_cache_between_calls(self):
        q=Reader("carrier",self.encoded)
        self.load(q);self.load(q)
        self.assertEqual(q.reads,2)
if __name__=="__main__":unittest.main()
