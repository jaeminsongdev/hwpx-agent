import base64
import copy
import hashlib
import io
import json
import unittest
import zlib
from unittest.mock import patch
import packed_receipt_json as d


class PackedReceiptTests(unittest.TestCase):
    def carrier(self, doc=None):
        return d.pack({'samples': [{'cpu': 99.0}], 'note': '한글\t x\n', 'failed': False}
            if doc is None else doc, lambda: None)[0]
    def raw(self, data):
        compressor = zlib.compressobj(1, zlib.DEFLATED, 31)
        blob = compressor.compress(data) + compressor.flush()
        return dict(schema_version=d.SCHEMA, codec='gzip-base64-canonical-ascii-json',
            compression_level=1, raw_json_bytes=len(data), raw_json_sha256=hashlib.sha256(data).hexdigest(),
            gzip_bytes=len(blob), payload_base64=base64.b64encode(blob).decode('ascii'))
    def replace_blob(self, carrier, blob):
        return dict(carrier, gzip_bytes=len(blob), payload_base64=base64.b64encode(blob).decode('ascii'))
    def test_entire_value_order_samples_unicode_spaces_and_original_are_retained(self):
        doc = {'state': 'FAILED_NOT_ACCEPTED', 'samples': [{'cpu': 99, 'ram': 43.1}],
            'nested': [None, True, -1.25], 'text': '  한글 😀\t\n  ', 'stop': 'STOP_CPU'}
        original = copy.deepcopy(doc)
        decoded = d.unpack(self.carrier(doc), lambda: None)
        self.assertEqual(decoded, original)
        self.assertEqual(doc, original)
        self.assertEqual(list(decoded), list(original))
    def test_large_value_roundtrips_with_bounded_carrier_writes(self):
        doc = {'text': 'x' * (3 * d.INFLATE_BYTES)}
        stream = io.StringIO()
        stats = d.dump(doc, stream, checkpoint=lambda: None, indent=2)
        self.assertEqual(d.unpack(json.loads(stream.getvalue()), lambda: None), doc)
        self.assertLessEqual(stats['carrier_write_statistics']['maximum_write_batch_chars'], 32768)
        self.assertLess(stats['carrier_bytes'], stats['raw_json_bytes'])
    def test_codec_shape_and_unknown_keys_fail(self):
        carrier = self.carrier()
        for wrong in (dict(carrier, other=1), dict(carrier, codec='zlib'), dict(carrier, compression_level=9)):
            with self.assertRaises(ValueError):
                d.unpack(wrong, lambda: None)
    def test_declared_sizes_are_exact_ints_bounded_before_inflate(self):
        carrier = self.carrier()
        for size in (True, 0, -1, d.MAX_BYTES + 1):
            with self.assertRaises(ValueError):
                d.unpack(dict(carrier, raw_json_bytes=size), lambda: None)
    def test_invalid_base64_is_rejected(self):
        with self.assertRaises(ValueError):
            d.unpack(dict(self.carrier(), payload_base64='???'), lambda: None)
    def test_base64_whitespace_or_wrong_gzip_size_is_rejected(self):
        carrier = self.carrier()
        for wrong in (dict(carrier, payload_base64=carrier['payload_base64'] + '\n'),
                dict(carrier, gzip_bytes=carrier['gzip_bytes'] + 1)):
            with self.assertRaises(ValueError):
                d.unpack(wrong, lambda: None)
    def test_corrupt_gzip_checksum_is_rejected(self):
        carrier = self.carrier()
        blob = bytearray(base64.b64decode(carrier['payload_base64']))
        blob[-1] ^= 1
        with self.assertRaises(ValueError):
            d.unpack(self.replace_blob(carrier, blob), lambda: None)
    def test_truncated_gzip_is_rejected(self):
        carrier = self.carrier()
        blob = base64.b64decode(carrier['payload_base64'])[:-4]
        with self.assertRaises(ValueError):
            d.unpack(self.replace_blob(carrier, blob), lambda: None)
    def test_trailing_and_concatenated_members_are_rejected(self):
        carrier = self.carrier()
        blob = base64.b64decode(carrier['payload_base64'])
        for extra in (b'\x00', blob):
            with self.assertRaises(ValueError):
                d.unpack(self.replace_blob(carrier, blob + extra), lambda: None)
    def test_inflate_over_declared_length_stops(self):
        with self.assertRaisesRegex(ValueError, 'INFLATE_LENGTH'):
            d.unpack(dict(self.carrier({'v': 'x' * 100000}), raw_json_bytes=1), lambda: None)
    def test_wrong_raw_sha_and_size_fail(self):
        carrier = self.carrier()
        for wrong in (dict(carrier, raw_json_sha256='0' * 64),
                dict(carrier, raw_json_bytes=carrier['raw_json_bytes'] + 1)):
            with self.assertRaises(ValueError):
                d.unpack(wrong, lambda: None)
    def test_noncanonical_inner_json_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'EXACT_CANONICAL'):
            d.unpack(self.raw(b'{ "a": 1 }'), lambda: None)
    def test_duplicate_inner_keys_are_rejected(self):
        with self.assertRaisesRegex(ValueError, 'EXACT_CANONICAL'):
            d.unpack(self.raw(b'{"a":1,"a":2}'), lambda: None)
    def test_original_CPU_RAM_IO_stops_are_not_swallowed(self):
        carrier = self.carrier()
        for reason in ('STOP_SUSTAINED_SYSTEM_CPU', 'STOP_LOW_AVAILABLE_RAM', 'STOP_SQL_IO_SCOPE_TIME'):
            def stop():
                raise ValueError(reason)
            with self.assertRaisesRegex(ValueError, reason):
                d.pack({}, stop)
            with self.assertRaisesRegex(ValueError, reason):
                d.unpack(carrier, stop)
    def test_short_carrier_write_is_not_retried(self):
        class Stream:
            def __init__(self):
                self.calls = 0
            def write(self, text):
                self.calls += 1
                return len(text) - 1
        stream = Stream()
        with self.assertRaises(ValueError):
            d.dump({}, stream, checkpoint=lambda: None)
        self.assertEqual(stream.calls, 1)
    def test_raw_budget_nonfinite_values_and_cycles_fail(self):
        with patch.object(d, 'MAX_BYTES', 64), self.assertRaisesRegex(ValueError, 'RAW_JSON_BUDGET'):
            d.pack({'v': 'x' * 256}, lambda: None)
        with self.assertRaises(ValueError):
            d.pack({'v': float('nan')}, lambda: None)
        cycle = []
        cycle.append(cycle)
        with self.assertRaises(ValueError):
            d.pack(cycle, lambda: None)
