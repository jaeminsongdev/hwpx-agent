import json
import unittest
from types import SimpleNamespace as NS

MODULE=None
RAW=None


class Tests(unittest.TestCase):
    def test_real_original_and_failed_semantics_preserved(self):
        MODULE.exact_original(MODULE.ORIGINAL,RAW)
        MODULE.failed_state(json.loads(RAW))

    def test_any_original_byte_or_pin_substitution_rejected(self):
        for raw in (RAW[:-1],RAW+b' ',b'not an original'):
            with self.assertRaises(ValueError):MODULE.exact_original(MODULE.ORIGINAL,raw)
        with self.assertRaises(ValueError):MODULE.exact_original(dict(MODULE.ORIGINAL,sha256='0'*64),RAW)

    def test_failed_state_cannot_be_promoted_or_other_case(self):
        original=json.loads(RAW)
        for key,value in (('state','PASS'),('selected_test_index',164),('product_complete',True),
                          ('actual_product_child_executed',False),('current_generation_runtime_candidate_qualified',True)):
            with self.assertRaises(ValueError):MODULE.failed_state(dict(original,**{key:value}))

    def test_only_explicit_new_failure_generation_names(self):
        name=MODULE.destination(1)
        self.assertIn('case165-runtime-run008.failed.strict-window.xz8m-g001',name)
        self.assertNotEqual(name,MODULE.ORIGINAL['path'])
        for value in (0,9,True,'1'):
            with self.assertRaises(ValueError):MODULE.destination(value)

    def test_physical_proposal_not_relabelled_as_raw_or_ordinary(self):
        pin=MODULE.proposal(b'candidate',1)
        self.assertEqual(pin['bytes'],9);self.assertNotEqual(pin['sha256'],MODULE.ORIGINAL['sha256'])
        self.assertIn('.failed.',pin['path'])
        for value in (b'',bytearray(b'a')):
            with self.assertRaises(ValueError):MODULE.proposal(value,1)

    def test_decoder_reader_preserves_physical_return_and_two_real_calls(self):
        physical=dict(path='carrier',bytes=3,sha256='physical');calls=[];counts=[]
        class Reader:
            def _read(self,name,parse=False):calls.append((name,parse));return physical,bytearray(b'abc') if parse else None
        budget=NS(run=lambda operation:operation(lambda:None))
        codec=NS(decode=lambda raw,check:RAW)
        reader=MODULE.decoder_reader(Reader,'carrier',budget,codec,counts)()
        self.assertEqual(reader._read('carrier'),(physical,None))
        self.assertEqual(reader._read('carrier',True),(physical,bytearray(b'abc')))
        self.assertEqual(calls,[('carrier',True),('carrier',True)]);self.assertEqual(counts,[physical,physical])

    def test_decoder_failure_never_becomes_completed_boundary(self):
        class Reader:
            def _read(self,name,parse=False):return {},bytearray(b'abc')
        counts=[];budget=NS(run=lambda operation:operation(lambda:None));codec=NS(decode=lambda raw,check:b'wrong')
        reader=MODULE.decoder_reader(Reader,'carrier',budget,codec,counts)()
        with self.assertRaises(ValueError):reader._read('carrier')
        self.assertEqual(counts,[])
