import base64
import hashlib
import json
import sys
import unittest
import zlib
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import runtime_record_envelope_v2 as m

class Tests(unittest.TestCase):
    def envelope(self,raw=b'{"value":1}\n'):
        return json.loads(m.encode(raw,lambda:None))
    def decode(self,row):return m.decode(json.dumps(row).encode(),lambda:None)
    def test_original_bytes_whitespace_unicode_and_float_types_round_trip(self):
        raw=' {"한글": [0.0, 1, true, null], "bytes": "원본"}\r\n'.encode()
        self.assertEqual(m.decode(m.encode(raw,lambda:None),lambda:None),raw)
        self.assertIs(type(json.loads(m.decode(m.encode(raw,lambda:None),lambda:None))["한글"][0]),float)
    def test_boundary_sizes_are_exact_and_checkpoints_not_skipped(self):
        for size in (1,m.CHUNK_BYTES-1,m.CHUNK_BYTES,m.CHUNK_BYTES+1,2*m.CHUNK_BYTES+3):
            calls=[];raw=b"x"*size;packed=m.encode(raw,lambda:calls.append(1))
            self.assertEqual(m.decode(packed,lambda:calls.append(1)),raw);self.assertGreater(len(calls),7)
    def test_encode_uses_low_cost_level1_and_no_external_io(self):
        original=zlib.compressobj
        with patch.object(zlib,"compressobj",wraps=original) as create:
            m.encode(b"a"*1000,lambda:None);create.assert_called_once_with(level=1)
    def test_wrong_schema_encoding_and_extra_fields_rejected(self):
        for key,value in (("schema_version","plain-json"),("encoding","identity"),("extra",1)):
            row=self.envelope();row[key]=value
            with self.assertRaises(ValueError):self.decode(row)
    def test_declared_size_bool_zero_negative_and_oversize_rejected(self):
        for value in (True,0,-1,m.MAX_BYTES+1):
            row=self.envelope();row["original_bytes"]=value
            with self.assertRaises(ValueError):self.decode(row)
    def test_hash_tampering_and_invalid_shapes_rejected(self):
        for value in ("0"*64,"g"*64,None,12):
            row=self.envelope();row["original_sha256"]=value
            with self.assertRaises(ValueError):self.decode(row)
    def test_truncation_and_concatenated_stream_rejected(self):
        row=self.envelope(b"a"*10000);compressed=base64.b64decode(row["payload"])
        for value in (compressed[:-1],compressed+b"tail",compressed+zlib.compress(b"second")):
            bad=dict(row,payload=base64.b64encode(value).decode())
            with self.assertRaises(ValueError):self.decode(bad)
    def test_large_expansion_cannot_exceed_small_declared_limit(self):
        row=self.envelope(b"a"*(3*m.CHUNK_BYTES));row["original_bytes"]=10
        with self.assertRaisesRegex(ValueError,"EXPANSION_EXCEEDS_DECLARED_SIZE"):self.decode(row)
    def test_base64_json_and_duplicate_key_rejected(self):
        row=self.envelope();row["payload"]="???"
        with self.assertRaises(ValueError):self.decode(row)
        for raw in (b"not json",b'{"schema_version":1,"schema_version":2}'):
            with self.assertRaises(ValueError):m.decode(raw,lambda:None)
    def test_guard_error_identity_before_encode_or_decode(self):
        error=ValueError("ORIGINAL_GUARD_STOP")
        def fail():raise error
        for function,raw in ((m.encode,b"a"),(m.decode,m.encode(b"a",lambda:None))):
            with self.assertRaises(ValueError) as ctx:function(raw,fail)
            self.assertIs(ctx.exception,error)
    def test_guard_error_mid_encode_not_resumed(self):
        calls=[];error=ValueError("STOP")
        def guard():
            calls.append(1)
            if len(calls)==3:raise error
        with self.assertRaises(ValueError) as ctx:m.encode(b"a"*(3*m.CHUNK_BYTES),guard)
        self.assertIs(ctx.exception,error);self.assertEqual(len(calls),3)
    def test_each_call_decodes_fresh_no_state_or_byte_cache(self):
        first=m.encode(b"first",lambda:None);second=m.encode(b"second",lambda:None)
        self.assertEqual(m.decode(first,lambda:None),b"first")
        self.assertEqual(m.decode(second,lambda:None),b"second")


    def test_expanded_output_call_never_exceeds64KiB(self):
        original=zlib.decompressobj;limits=[];lengths=[]
        class Observed:
            def __init__(self):self.inner=original()
            def decompress(self,data,limit):
                limits.append(limit);out=self.inner.decompress(data,limit)
                lengths.append(len(out));return out
            def __getattr__(self,key):return getattr(self.inner,key)
        raw=b"x"*(8*m.CHUNK_BYTES+3);packed=m.encode(raw,lambda:None)
        with patch.object(zlib,"decompressobj",side_effect=Observed):
            self.assertEqual(m.decode(packed,lambda:None),raw)
        self.assertGreaterEqual(len(limits),9)
        self.assertLessEqual(max(limits),m.CHUNK_BYTES)
        self.assertLessEqual(max(lengths),m.CHUNK_BYTES)

    def test_guard_can_stop_inside_single_high_expansion_input_chunk(self):
        packed=m.encode(b"x"*(8*m.CHUNK_BYTES),lambda:None)
        self.assertLess(len(base64.b64decode(json.loads(packed)["payload"])),m.CHUNK_BYTES)
        calls=[];error=ValueError("ORIGINAL_EXPANSION_GUARD_STOP")
        def guard():
            calls.append(1)
            if len(calls)==4:raise error
        with self.assertRaises(ValueError) as ctx:m.decode(packed,guard)
        self.assertIs(ctx.exception,error);self.assertEqual(len(calls),4)

    def test_exact_output_chunk_multiple_and_binary_bytes(self):
        raw=bytes(range(256))*(m.CHUNK_BYTES//256*3)
        self.assertEqual(m.decode(m.encode(raw,lambda:None),lambda:None),raw)

    def test_truncated_stream_after_multiple_expanded_chunks_rejected(self):
        row=self.envelope(b"x"*(8*m.CHUNK_BYTES))
        row["payload"]=base64.b64encode(base64.b64decode(row["payload"])[:-1]).decode()
        with self.assertRaisesRegex(ValueError,"TRUNCATED_COMPRESSED_STREAM"):self.decode(row)

if __name__=="__main__":unittest.main()
