import json
import unittest
from types import SimpleNamespace as NS

MODULE=None
RAW=None
CODEC=None
CHECK=None


class Tests(unittest.TestCase):
    def test_exact_raw_and_original_failure(self):
        MODULE.exact_original(MODULE.ORIGINAL,RAW);MODULE.failed_state(json.loads(RAW))

    def test_no_raw_byte_or_pin_substitution(self):
        for raw in (RAW[:-1],RAW+b' ',b'invalid'):
            with self.assertRaises(ValueError):MODULE.exact_original(MODULE.ORIGINAL,raw)
        with self.assertRaises(ValueError):MODULE.exact_original(dict(MODULE.ORIGINAL,bytes=1),RAW)

    def test_no_acceptance_prebody_unknown_or_wrong_context_reclassification(self):
        row=json.loads(RAW)
        for key,value in (('state','PASS'),('selected_test_index',True),('selected_test_index',164),
            ('actual_product_child_executed',False),('actual_product_child_executed',None),
            ('product_complete',True),('current_generation_runtime_candidate_qualified',True),
            ('stop_reason','STOP_STRICT_PRODUCT_WINDOW'),('operation_phase','before_product')):
            with self.assertRaises(ValueError):MODULE.failed_state(dict(row,**{key:value}))

    def test_explicit_separate_finite_generation(self):
        self.assertIn('run007.failed.final-source.xz8m-g001',MODULE.destination(1))
        self.assertNotEqual(MODULE.destination(1),MODULE.ORIGINAL['path'])
        for value in (0,9,True,'1'):
            with self.assertRaises(ValueError):MODULE.destination(value)

    def test_two_physical_reader_calls_not_cached(self):
        pin=dict(path='carrier',bytes=3,sha256='abc');calls=[];counts=[]
        class Reader:
            def _read(self,name,parse=False):calls.append((name,parse));return pin,bytearray(b'abc') if parse else None
        budget=NS(run=lambda operation:operation(lambda:None));codec=NS(decode=lambda raw,check:RAW)
        reader=MODULE.reader_type(Reader,pin,budget,codec,counts)()
        self.assertEqual(reader._read('carrier'),(pin,None))
        self.assertEqual(reader._read('carrier',True),(pin,bytearray(b'abc')))
        self.assertEqual(calls,[('carrier',True),('carrier',True)]);self.assertEqual(counts,[pin,pin])

    def test_mismatched_physical_pin_rejected_before_decoder(self):
        class Reader:
            def _read(self,name,parse=False):return dict(path='carrier',bytes=1),b'x'
        def denied(operation):raise AssertionError('decoder must not run')
        reader=MODULE.reader_type(Reader,dict(path='carrier',bytes=2),NS(run=denied),None,[])()
        with self.assertRaises(ValueError):reader._read('carrier')

    def test_failed_decode_never_counts_complete(self):
        pin=dict(path='carrier');counts=[]
        class Reader:
            def _read(self,name,parse=False):return pin,b'x'
        reader=MODULE.reader_type(Reader,pin,NS(run=lambda op:op(lambda:None)),NS(decode=lambda raw,check:b'wrong'),counts)()
        with self.assertRaises(ValueError):reader._read('carrier')
        self.assertEqual(counts,[])

    def test_noncarrier_return_not_relabelled(self):
        class Reader:
            def _read(self,name,parse=False):return dict(path=name),b'x' if parse else None
        reader=MODULE.reader_type(Reader,dict(path='carrier'),None,None,[])()
        self.assertEqual(reader._read('other'),(dict(path='other'),None))

    def test_original_format_and_noncanonical_json_bytes_preserved(self):
        # Codec round trip operates on opaque bytes, not parsed/rewritten JSON.
        raw=b' { "z": 2, "a":1 }\r\n'
        self.assertEqual(CODEC.decode(CODEC.encode(raw,CHECK),CHECK),raw)
