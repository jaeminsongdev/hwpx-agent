import copy
import unittest

MODULE=None


def fixture():
    rows=[dict(semantic_original_pin=dict(path=f'implementation/p09/evidence/p09-361-case{i}-current-runtime-run{n:03}.v1.json'),
        physical_envelope_pin=dict(path=f'old/{i}-{n}.envelope.v1.json')) for i,n in MODULE.KEYS]
    rows.extend(dict(semantic_original_pin=dict(path=f'other/{n}.json'),physical_envelope_pin=dict(path=f'physical/{n}.json')) for n in range(68))
    return rows


class Tests(unittest.TestCase):
    def test_only_exact_seven_existing_semantic_receipts(self):
        rows=fixture(); picked=MODULE.choose(rows)
        self.assertEqual(len(picked),7); self.assertEqual(picked,rows[:7])
    def test_full75_and_unique_originals_required(self):
        rows=fixture()
        for value in (rows[:7],rows+[rows[0]],rows[:-1]+[rows[0]]):
            with self.assertRaises(ValueError): MODULE.choose(value)
    def test_missing_seventh_is_not_replaced_by_another_record(self):
        rows=fixture(); rows[6]['semantic_original_pin']['path']='other/unrelated.json'
        with self.assertRaises(ValueError): MODULE.choose(rows)
    def test_source_descriptor_table_is_never_mutated(self):
        rows=fixture(); original=copy.deepcopy(rows); result=MODULE.choose(rows)
        result[0]['physical_envelope_pin']['path']='changed'
        self.assertEqual(rows,original)
    def test_repack_destination_is_separate_and_finite(self):
        original=fixture()[0]['semantic_original_pin']; value=MODULE.destination(original,1)
        self.assertIn('/legacy-zlib75/',value); self.assertNotEqual(value,original['path'])
        self.assertTrue(value.endswith('.envelope.v1.json'))
        for generation in (True,0,9):
            with self.assertRaises(ValueError): MODULE.destination(original,generation)
    def test_generic_metadata_or_other_current_runtime_is_forbidden(self):
        for path in ('tools/p09/source.py','implementation/p09/evidence/p09-361-case165-preflight.v1.json',
                'implementation/p09/evidence/p09-361-case165-current-runtime-run009.v1.json'):
            with self.assertRaises(ValueError): MODULE.destination(dict(path=path),1)


if __name__=='__main__': unittest.main()
