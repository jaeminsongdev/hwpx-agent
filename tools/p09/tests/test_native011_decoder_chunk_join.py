"""Retained original decoder contracts plus candidate-storage regressions."""
import hashlib
from pathlib import Path
from types import FunctionType
import unittest
import runtime_record_envelope_v2 as original
import native011_decoder_chunk_join as candidate
import test_runtime_record_envelope_v2 as retained

RAW=(Path(__file__).resolve().parents[3]/candidate.SOURCE['path']).read_bytes()
CODEC,PROOF=candidate.connect(RAW,original)

# Whole original test bodies and helpers, with only their explicit codec
# dependency changed. Do not patch a default source module or omit contracts.
methods={'__module__':__name__}
for name,fn in vars(retained.Tests).items():
    if type(fn) is FunctionType:
        clone=FunctionType(fn.__code__,dict(fn.__globals__,m=CODEC),argdefs=fn.__defaults__,closure=fn.__closure__)
        clone.__kwdefaults__=fn.__kwdefaults__;methods[name]=clone
PreservedCodecContracts=type('PreservedCodecContracts',(unittest.TestCase,),methods)


class ChunkJoinContracts(unittest.TestCase):
    def test_full_original_inverse_and_no_wire_or_budget_relaxation(self):
        self.assertTrue(PROOF['exact_original_decoder_AST_inverse'])
        self.assertTrue(PROOF['original_guard_positions_hashes_and_all_rejections_retained'])
        self.assertFalse(PROOF['installed_in_Runtime']);self.assertIs(CODEC.encode,original.encode)

    def test_changed_or_nonbytes_source_is_rejected(self):
        for raw in (RAW+b'\n',RAW.decode(),b''):
            with self.assertRaisesRegex(ValueError,'EXACT_ENTIRE_ORIGINAL'):candidate.connect(raw,original)

    def test_original_and_candidate_have_identical_fresh_output_hash_and_guard_count(self):
        for raw in (b'x',bytes(range(256))*257,b'a'*(5*65536+1)):
            encoded=original.encode(raw,lambda:None);traces=[]
            for decode in (original.decode,CODEC.decode):
                calls=[];actual=decode(encoded,lambda:calls.append(1))
                self.assertEqual(actual,raw);self.assertIs(type(actual),bytes)
                self.assertEqual(hashlib.sha256(actual).digest(),hashlib.sha256(raw).digest())
                traces.append(len(calls))
            self.assertEqual(traces[0],traces[1])

    def test_original_default_decoder_and_namespace_remain_unchanged(self):
        saved=dict(vars(original));decode=original.decode
        candidate.connect(RAW,original)
        self.assertIs(original.decode,decode)
        self.assertTrue(all(vars(original)[name] is value for name,value in saved.items()))

    def test_all_original_contract_function_bodies_and_helpers_retained(self):
        names=[name for name in vars(retained.Tests) if name.startswith('test_')]
        self.assertEqual(len(names),16)
        for name,fn in vars(retained.Tests).items():
            if type(fn) is FunctionType:
                actual=vars(PreservedCodecContracts)[name]
                self.assertIs(actual.__code__,fn.__code__);self.assertIs(actual.__closure__,fn.__closure__)
