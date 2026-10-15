"""Bounded fixtures; no Native/product acceptance is inferred."""
import hashlib
import unittest
from types import SimpleNamespace as NS
import fresh_lossless_metadata_reader_v1 as m

CHECKPOINT=lambda:None


class Base:
    def __init__(self):
        self.checkpoint=CHECKPOINT;self.maximum_parse_bytes=64;self.calls=[];self.contents=b"physical"
        self.read_passes=self.bytes_read=0
    def _read(self,name,parse=False):
        self.checkpoint();self.calls.append((name,parse));self.read_passes+=1;self.bytes_read+=len(self.contents)
        return dict(path=name,bytes=len(self.contents),sha256=hashlib.sha256(self.contents).hexdigest()),bytearray(self.contents) if parse else None


class Tests(unittest.TestCase):
    def setUp(self):
        CHECKPOINT();self.logical=b'{"a":1}';self.decoded=[]
        self.old=dict(path="semantic",bytes=len(self.logical),sha256=hashlib.sha256(self.logical).hexdigest())
        self.new=dict(path="physical",bytes=8,sha256=hashlib.sha256(b"physical").hexdigest())
        self.projection=NS(next_case=164,semantic_pins={"semantic":self.old},physical_pins={"physical":self.new},
            decode_fresh=lambda name,pin,raw,checkpoint:(self.decoded.append(bytes(raw)) or self.logical))
        self.rows=[dict(schema_version="fixture",semantic_original_pin=self.old,physical_envelope_pin=self.new,next_case=164)]
        self.Reader=m.reader_type(Base,self.projection,self.rows)
    def tearDown(self):CHECKPOINT()
    def test_fresh_read_and_decode_per_request_no_cache(self):
        r=self.Reader()
        self.assertEqual(r._read("semantic",True),(self.old,bytearray(self.logical)))
        self.assertEqual(r._read("semantic"),(self.old,None))
        self.assertEqual(r.calls,[("physical",True),("physical",True)])
        self.assertEqual(len(self.decoded),2)
    def test_unmapped_reader_is_original(self):
        r=self.Reader();r._read("other",True)
        self.assertEqual(r.calls,[("other",True)]);self.assertEqual(self.decoded,[])
    def test_physical_counter_not_decoded_bytes(self):
        r=self.Reader();r._read("semantic",True)
        self.assertEqual(r.bytes_read,8)
        row=m.summary(r)
        self.assertEqual(row["mapped_physical_bytes_read"],8)
        self.assertEqual(row["mapped_semantic_bytes_restored"],7)
    def test_changed_physical_bytes_rejected(self):
        r=self.Reader();r.contents=b"tampered"
        with self.assertRaisesRegex(ValueError,"ACTUAL_FRESH_PHYSICAL_PIN"):r._read("semantic")
        self.assertEqual(self.decoded,[])
    def test_wrong_restored_hash_rejected(self):
        r=self.Reader();self.logical=b"wrong"
        with self.assertRaisesRegex(ValueError,"EXACT_FRESH_SEMANTIC_BYTES"):r._read("semantic")
        self.assertEqual(r.lossless_metadata_completed,0)
    def test_original_parse_budget_before_decode(self):
        r=self.Reader();r.maximum_parse_bytes=1
        with self.assertRaisesRegex(ValueError,"ORIGINAL_PARSE_BUDGET"):r._read("semantic",True)
        self.assertEqual(r.calls,[])
    def test_collision_or_wrong_projection_rejected(self):
        for rows in (self.rows*2,[dict(self.rows[0],next_case=165)],[]):
            with self.assertRaises(ValueError):m.reader_type(Base,self.projection,rows)
    def test_decoder_error_not_replaced_by_prior_success(self):
        r=self.Reader();r._read("semantic")
        def fail(*args):raise ValueError("fixture_decode_error")
        self.projection.decode_fresh=fail
        with self.assertRaisesRegex(ValueError,"fixture_decode_error"):r._read("semantic")
        self.assertEqual(len(r.calls),2)
        self.assertEqual((r.lossless_metadata_attempts,r.lossless_metadata_completed),(2,1))


if __name__=="__main__":unittest.main()
