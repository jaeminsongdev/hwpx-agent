"""Exact bounded expansion and unchanged original worker checks."""
import copy
import hashlib
import json
from pathlib import Path
import sys
from types import SimpleNamespace as NS
import unittest
sys.path.insert(0,str(Path(__file__).parents[1]))
import bounded_successor_capsule_wire_v2 as m
import compact_worker_capsule_wire_v1 as compact


def row(n=48):
    def pin(path):return dict(path=path,bytes=100,sha256=hashlib.sha256(path.encode()).hexdigest())
    return dict(schema_version="capsule/v1",next_case=160,accepted_count_before=153,
        manifest_pin=pin("manifest"),authority_pin=pin("authority"),prior_runtime_pin=pin("prior"),
        descriptors=[dict(schema_version="descriptor/v1",next_case=160,
            semantic_original_pin=pin(f"implementation/p09/evidence/p09-361-case{i+112:03}-current-runtime-run001.v1.json"),
            physical_envelope_pin=pin(f"implementation/p09/evidence/p361-lossless-runtime-inputs/case{i+112:03}-runtime-run001.envelope.v1.json")) for i in range(n)])


class Tests(unittest.TestCase):
    def test_all_current_48_rows_exactly_restored_under_original_transport_limit(self):
        value=row(48);packed=compact.pack(value);before=copy.deepcopy(packed)
        encoded=m.encode_compact(packed,lambda:None)
        self.assertLessEqual(len(encoded),16384)
        self.assertEqual(compact.unpack(m.decode_compact(encoded,lambda:None)),value)
        self.assertEqual(packed,before)
    def test_oversized_transport_and_expansion_rejected(self):
        with self.assertRaises(ValueError):m.decode_compact(" "*16385,lambda:None)
        with self.assertRaises(ValueError):m.encode_compact(dict(data="x"*m.MAX_EXPANDED_BYTES),lambda:None)
        # Row admission bound is not a promise that arbitrary independent hashes
        # can fit the transport. Oversized graphs must fail, never lose rows.
        with self.assertRaises(ValueError):m.encode_compact(compact.pack(row(249)),lambda:None)
    def test_tampered_hash_trailing_stream_and_boolean_size_rejected(self):
        encoded=m.encode_compact(compact.pack(row()),lambda:None)
        for key,value in (("raw_sha256","0"*64),("raw_bytes",True),("zlib_base64","invalid!")):
            wire=json.loads(encoded);wire[key]=value
            with self.assertRaises(ValueError):m.decode_compact(json.dumps(wire,separators=(",",":")),lambda:None)
    def test_original_stop_not_swallowed(self):
        error=ValueError("ORIGINAL_RESOURCE_STOP")
        def stop():raise error
        with self.assertRaises(ValueError) as caught:m.encode_compact(compact.pack(row()),stop)
        self.assertIs(caught.exception,error)
    def test_duplicate_keys_and_extra_fields_rejected(self):
        encoded=m.encode_compact(compact.pack(row()),lambda:None)
        def unique(pairs):
            result={}
            for name,value in pairs:
                if name in result:raise ValueError("DUPLICATE")
                result[name]=value
            return result
        with self.assertRaises(ValueError):m.decode_compact('{"schema_version":"a",'+encoded[1:],lambda:None,object_pairs_hook=unique)
        wire=json.loads(encoded);wire["extra"]=0
        with self.assertRaises(ValueError):m.decode_compact(json.dumps(wire),lambda:None)


if __name__=="__main__":unittest.main()
