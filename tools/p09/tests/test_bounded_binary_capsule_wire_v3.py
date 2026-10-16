import hashlib
import json
import lzma
import unittest

M=CHECK=None


def fixture(count=3):
    pin=lambda i:['implementation/p09/evidence/unicode-한글-'+str(i)+'.json',i+1,hashlib.sha256(str(i).encode()).hexdigest()]
    return dict(schema_version=M.COMPACT_SCHEMA,context=['original-current-schema',165,158],
        descriptor_context=['original-descriptor-schema',165],manifest=pin(0),authority=pin(1),prior=pin(2),
        bindings=[[pin(3+i),pin(3+count+i)] for i in range(count)])


class Tests(unittest.TestCase):
    def setUp(self): CHECK()
    def tearDown(self): CHECK()
    def test_all_fields_unicode_order_and_hashes_roundtrip_without_external_IO(self):
        row=fixture(); wire=M.encode_compact(row,CHECK)
        self.assertEqual(M.decode_compact(wire,CHECK,object_pairs_hook=M.unique),row)
        self.assertEqual(M.unpack_binary(M.pack_binary(row,CHECK),CHECK),row)
    def test_all_249_binary_rows_are_preserved_even_if_transport_rejects_size(self):
        row=fixture(249); raw=M.pack_binary(row,CHECK)
        self.assertEqual(M.unpack_binary(raw,CHECK),row)
    def test_malformed_and_too_many_pairs_reject(self):
        for row in (dict(fixture(),extra=1),dict(fixture(),bindings=[]),fixture(250),dict(fixture(),context=['x',True,158])):
            with self.assertRaises(ValueError): M.pack_binary(row,CHECK)
    def test_pin_types_hashes_and_large_paths_reject(self):
        for pin in (['x',True,'0'*64],['x',0,'0'*64],['x',1,'G'*64],['x'*16385,1,'0'*64]):
            with self.assertRaises(ValueError): M.pack_binary(dict(fixture(),manifest=pin),CHECK)
    def test_uint_is_bounded_and_overlong_form_rejects(self):
        for value in (0,127,128,16384,2**63-1): self.assertEqual(M.Cursor(M.uint(value)).uint(),value)
        for data in (b'\x80\x00',b'\x80'*9,b''):
            with self.assertRaises(ValueError): M.Cursor(data).uint()
        for value in (True,-1,2**63):
            with self.assertRaises(ValueError): M.uint(value)
    def test_truncated_and_trailing_binary_bytes_reject(self):
        raw=M.pack_binary(fixture(),CHECK)
        for changed in (raw[:-1],raw+b'tail',b'WRONG!'+raw[6:]):
            with self.assertRaises(ValueError): M.unpack_binary(changed,CHECK)
    def test_seven_bit_inverse_padding_wrong_hash_and_version_reject(self):
        for raw in (bytes(range(256)),b'\x00',b'\xff'*127): self.assertEqual(M.seven_decode(M.seven_encode(raw)),raw)
        with self.assertRaises(ValueError): M.seven_decode(M.seven_encode(b'\x00')[:-1]+'\x01')
        wire=M.encode_compact(fixture(),CHECK); body=M.seven_decode(wire[len(M.WIRE_MAGIC):])
        changed=bytes([body[0]^1])+body[1:]
        with self.assertRaises(ValueError): M.decode_compact(M.WIRE_MAGIC+M.seven_encode(changed),CHECK)
        with self.assertRaises(ValueError): M.decode_compact('WRONG:'+wire[6:],CHECK)
        with self.assertRaises(ValueError): M.unique([('x',1),('x',2)])
    def test_xz_truncation_trailing_concatenation_and_expansion_reject(self):
        body=M.wire_body(fixture(),CHECK); c=M.Cursor(body); digest=c.take(32); size,hashes,length=c.uint(),c.uint(),c.uint()
        compressed=c.take(length); digests=c.take(hashes)
        for changed in (compressed[:-1],compressed+b'tail',compressed+compressed,lzma.compress(b'x'*131073)):
            altered=digest+M.uint(size)+M.uint(hashes)+M.uint(len(changed))+changed+digests
            with self.assertRaises(ValueError): M.decode_compact(M.WIRE_MAGIC+M.seven_encode(altered),CHECK)
    def test_original_resource_stop_is_not_retried_or_suppressed(self):
        calls=[]; failure=ValueError('SYNTHETIC_ORIGINAL_RESOURCE_STOP')
        def stopped(): calls.append(1); raise failure
        with self.assertRaises(ValueError) as caught: M.encode_compact(fixture(),stopped)
        self.assertIs(caught.exception,failure); self.assertEqual(calls,[1])
    def test_noncanonical_JSON_and_original_16k_ceiling_remain_closed(self):
        wire=M.encode_compact(fixture(),CHECK)
        with self.assertRaises(ValueError): M.decode_compact(wire+' ',CHECK,object_pairs_hook=M.unique)
        with self.assertRaises(ValueError): M.decode_compact(' '*16385,CHECK)
        self.assertEqual(M.MAX_BYTES,16384); self.assertEqual(M.MAX_EXPANDED_BYTES,131072)


if __name__=='__main__': unittest.main()
