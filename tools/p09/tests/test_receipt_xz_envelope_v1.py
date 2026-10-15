import base64
import hashlib
import json
from unittest.mock import patch
import unittest
import receipt_xz_envelope_v1 as MODULE


class Tests(unittest.TestCase):
    def fixture(self):return bytes(range(256))*1025+b"\x00\xff  exact whitespace\r\n"

    def change(self,encoded,**changes):
        row=json.loads(encoded);row.update(changes);return json.dumps(row).encode("ascii")

    def test_two_fresh_opaque_roundtrips_and_explicit_new_schema(self):
        raw=self.fixture();encoded=MODULE.encode(raw,lambda:None)
        first=MODULE.decode(encoded,lambda:None);second=MODULE.decode(encoded,lambda:None)
        self.assertEqual(first,raw);self.assertEqual(second,raw);self.assertIsNot(first,second)
        self.assertEqual(MODULE.encode(raw,lambda:None),encoded)
        self.assertEqual(json.loads(encoded)["encoding"],"xz-lzma2-base64")

    def test_bounds_types_old_format_extra_fields_and_duplicate_keys_rejected(self):
        encoded=MODULE.encode(b"safe",lambda:None)
        for raw in (b"",bytearray(b"safe")):
            with self.assertRaises(ValueError):MODULE.encode(raw,lambda:None)
        for key,value in (("original_bytes",True),("original_bytes",MODULE.MAX_BYTES+1),
            ("schema_version","hwpx-agent.p09-runtime-record-envelope/v1"),("encoding","zlib-base64"),
            ("original_sha256","z"*64),("payload","?"),("extra",True)):
            with self.subTest(key=key),self.assertRaises(ValueError):MODULE.decode(self.change(encoded,**{key:value}),lambda:None)
        with self.assertRaises(ValueError):MODULE.decode(b'{"payload":"x","payload":"y"}',lambda:None)

    def test_corrupt_hash_truncated_and_appended_frames_are_rejected(self):
        encoded=MODULE.encode(self.fixture(),lambda:None);row=json.loads(encoded)
        compressed=base64.b64decode(row["payload"])
        for payload in (compressed[:-1],compressed+b"tail",compressed+compressed):
            with self.assertRaises(ValueError):MODULE.decode(self.change(encoded,payload=base64.b64encode(payload).decode("ascii")),lambda:None)
        with self.assertRaises(ValueError):MODULE.decode(self.change(encoded,original_sha256="0"*64),lambda:None)

    def test_expansion_output_is_limited_before_returning_undeclared_bytes(self):
        encoded=MODULE.encode(b"x"*(3*MODULE.CHUNK_BYTES),lambda:None)
        with self.assertRaisesRegex(ValueError,"EXPANSION_EXCEEDS"):MODULE.decode(self.change(encoded,original_bytes=1),lambda:None)

    def test_native_decoder_receives_memory_and_chunk_limits(self):
        raw=self.fixture();encoded=MODULE.encode(raw,lambda:None);limits=[];original=MODULE.lzma.LZMADecompressor
        def create(*args,**kwargs):
            self.assertEqual(kwargs,dict(format=MODULE.lzma.FORMAT_XZ,memlimit=32*1024*1024))
            actual=original(*args,**kwargs)
            class Decoder:
                def __getattr__(self,name):return getattr(actual,name)
                def decompress(self,data,*,max_length):
                    limits.append(max_length);return actual.decompress(data,max_length=max_length)
            return Decoder()
        with patch.object(MODULE.lzma,"LZMADecompressor",side_effect=create):self.assertEqual(MODULE.decode(encoded,lambda:None),raw)
        self.assertGreater(len(limits),3);self.assertTrue(all(0<n<=64*1024 for n in limits))

    def test_guard_stop_is_not_suppressed_or_retried(self):
        calls=[]
        def stopped():calls.append(True);raise ValueError("ORIGINAL_STOP")
        with self.assertRaisesRegex(ValueError,"ORIGINAL_STOP"):MODULE.encode(b"data",stopped)
        self.assertEqual(calls,[True])
        encoded=MODULE.encode(b"data",lambda:None);calls.clear()
        with self.assertRaisesRegex(ValueError,"ORIGINAL_STOP"):MODULE.decode(encoded,stopped)
        self.assertEqual(calls,[True])
