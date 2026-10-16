"""Exact selection and honest metadata; no real legacy corpus imports."""
import copy
import hashlib
import unittest

MODULE=None


def pin(name,size=300000): return dict(path=name,bytes=size,sha256='0'*64)
def prior():
    return [dict(semantic_original_pin=pin(f'prior/{n}.json'),physical_envelope_pin=pin(f'physical/{n}.json')) for n in range(75)]


class Tests(unittest.TestCase):
    def test_exact_legacy_range_size_and_whole_source_pins(self):
        eligible=pin('implementation/p09/evidence/p09-180-example.actual-run01.v1.json')
        rows=[eligible,pin('implementation/p09/evidence/p09-361-case165-preflight.v1.json'),
            pin('implementation/p09/evidence/p09-139-example.v1.json'),pin('implementation/p09/evidence/p09-190-example.v1.json'),
            pin('implementation/p09/evidence/p09-180-small.v1.json',262143),pin('crates/source.rs'),
            pin('implementation/p09/evidence/source-archive/p09-180-example.v1.json')]
        self.assertEqual(MODULE.select(rows,prior()),[eligible])

    def test_no_duplicate_scope_or_old_alias_selection(self):
        item=pin('implementation/p09/evidence/p09-180-example.v1.json')
        with self.assertRaises(ValueError): MODULE.select([item,item],prior())
        table=prior(); table[0]['semantic_original_pin']=item
        with self.assertRaises(ValueError): MODULE.select([item],table)

    def test_missing_null_false_and_true_are_not_conflated(self):
        row=MODULE.observation(dict(state='STOPPED_NOT_ACCEPTED',product_complete=False,cleanup_confirmed=True,actual_product_child_executed=None))
        self.assertEqual(row['product_complete'],dict(present=True,value=False))
        self.assertEqual(row['cleanup_confirmed'],dict(present=True,value=True))
        self.assertEqual(row['actual_product_child_executed'],dict(present=True,value=None))
        self.assertEqual(row['product_body_observed'],dict(present=False,value=None))

    def test_failure_and_scoped_pass_not_promoted_or_rewritten(self):
        for state in ('STOPPED_NOT_ACCEPTED','PASS_SCOPED_NOT_GATE','NOT_RUN'):
            row=dict(schema_version='hwpx-agent.p09-trial/v1',state=state,product_complete=False)
            saved=copy.deepcopy(row); result=MODULE.observation(row)
            self.assertEqual(row,saved); self.assertEqual(result['state']['value'],state)

    def test_untyped_flags_state_and_pins_are_rejected(self):
        for row in (dict(product_complete=0),dict(state='arbitrary private text'),dict(schema_version='unknown')):
            with self.assertRaises(ValueError): MODULE.observation(row)
        for delta in (dict(bytes=True),dict(sha256='INVALID'),dict(extra='key')):
            with self.assertRaises(ValueError): MODULE.pin(dict(pin('p.json'),**delta))

    def test_byte_restoration_checks_every_byte_size_and_hash(self):
        raw=b'opaque\r\n{"unchanged": true}\n'
        expected=dict(path='p.json',bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
        MODULE.exact_bytes(raw,expected)
        for value in (raw+b' ',raw.replace(b'\r\n',b'\n'),b'X'+raw[1:]):
            with self.assertRaises(ValueError): MODULE.exact_bytes(value,expected)

    def test_destination_is_finite_separate_and_not_original(self):
        original=pin('implementation/p09/evidence/p09-180-example.v1.json')
        result=MODULE.destination(original,1)
        self.assertNotEqual(result,original['path']); self.assertTrue(result.endswith('.envelope.v1.json'))
        self.assertIn('/legacy-p140-189/',result)
        for generation in (True,0,9):
            with self.assertRaises(ValueError): MODULE.destination(original,generation)

    def test_candidate_count_and_cumulative_bytes_are_bounded(self):
        rows=[pin(f'implementation/p09/evidence/p09-180-example{n}.v1.json') for n in range(97)]
        with self.assertRaises(ValueError): MODULE.select(rows,prior())
        rows=[pin(f'implementation/p09/evidence/p09-180-example{n}.v1.json',16777216) for n in range(5)]
        with self.assertRaises(ValueError): MODULE.select(rows,prior())


if __name__=='__main__': unittest.main()
