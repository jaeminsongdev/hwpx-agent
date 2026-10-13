import copy
import unittest
from types import SimpleNamespace
from unittest.mock import patch
import runtime_fixture_inputs as f


class FixtureInputTests(unittest.TestCase):
    def setUp(self):
        self.p77=dict(actual_inputs=[dict(path=f'fixtures/p77-{i}.hwpx',bytes=1,sha256='a'*64) for i in range(36)])
        self.form=dict(cases=[dict(case=f'C{i}',source=dict(path=f's{i}.hwpx',bytes=1,sha256='a'*64),
            output=dict(path=f'o{i}.hwpx',bytes=1,sha256='a'*64)) for i in range(5)])
        self.note=dict(cases=[dict(case_id=key,file=f'{key}.hwpx',package_bytes=1,package_sha256='a'*64) for key in f.SLOTS])
        self.native=dict(state='failed_semantic_non_green',claims=dict(green_rows=0),cases=[
            dict(case_id=key,state='failed_semantic_non_green',snapshots={lane:dict(package_bytes=1,package_sha256='a'*64)
                for lane in ('saved','reopened')}) for key in f.SLOTS])
        self.header=dict(path=f.HEADER,bytes=1,sha256='a'*64)

    def build(self):return f.families(self.p77,self.form,self.note,self.native,self.header)

    def test_complete_known_family_counts_and_unique_pins(self):
        groups,inputs=self.build();self.assertEqual([len(groups[n]) for n in groups],[36,10,9,1,1,1])
        self.assertEqual(len(inputs),58);self.assertEqual(len(f.v.pins(list(inputs.values()))),58)

    def test_identical_cross_family_duplicate_deduplicated_not_skipped(self):
        groups,inputs=self.build();item=next(iter(inputs.values()))
        self.assertEqual(f.merge(dict(a=[item],b=[dict(item)])),{item['path']:item})

    def test_conflicting_duplicate_digest_rejected(self):
        item=f.pin('fixtures/a.hwpx',1,'a'*64)
        with self.assertRaises(ValueError):f.merge(dict(a=[item],b=[dict(item,sha256='b'*64)]))

    def test_path_escape_absolute_ADS_or_backslash_rejected(self):
        for path in ('../outside.hwpx','/outside.hwpx','C:/outside.hwpx','fixtures/a.hwpx:secret',r'fixtures\a.hwpx'):
            with self.assertRaises(ValueError):f.pin(path,1,'a'*64)

    def test_matrix_filename_scope_rejected(self):
        for name in ('../a.hwpx','a/b.hwpx',r'a\b.hwpx','C:a.hwpx',''):
            self.form['cases'][0]['source']['path']=name
            with self.assertRaises(ValueError):self.build()

    def test_negative_bool_zero_or_oversize_lengths_rejected(self):
        for value in (-1,True,0,f.MAX_FILE_BYTES+1):
            with self.assertRaises(ValueError):f.pin('fixtures/a.hwpx',value,'a'*64)

    def test_incomplete_P77_or_form_family_rejected(self):
        self.p77['actual_inputs'].pop()
        with self.assertRaises(ValueError):self.build()
        self.setUp();self.form['cases'].pop()
        with self.assertRaises(ValueError):self.build()

    def test_duplicate_note_cases_rejected(self):
        self.note['cases'][1]['case_id']=self.note['cases'][0]['case_id']
        with self.assertRaises(ValueError):self.build()

    def test_unknown_note_case_rejected(self):
        self.note['cases'][0]['case_id']='UNKNOWN'
        with self.assertRaises(ValueError):self.build()

    def test_note_failure_relabelled_to_pass_rejected(self):
        self.native['state']='PASS'
        with self.assertRaises(ValueError):self.build()
        self.setUp();self.native['cases'][0]['state']='PASS'
        with self.assertRaises(ValueError):self.build()

    def test_native_green_rows_or_bool_green_count_rejected(self):
        for value in (1,False):
            self.native['claims']['green_rows']=value
            with self.assertRaises(ValueError):self.build()

    def test_missing_saved_or_reopened_snapshot_rejected(self):
        del self.native['cases'][0]['snapshots']['reopened']
        with self.assertRaises(KeyError):self.build()

    def test_actual_hash_mismatch_rejected(self):
        item=f.pin('fixtures/a.hwpx',1,'a'*64)
        q=SimpleNamespace(pin=lambda name:dict(item,sha256='b'*64))
        with patch.object(f,'direct_file',return_value=None):
            with self.assertRaises(ValueError):f.verify_bytes(q,{item['path']:item})

    def test_each_unique_input_really_read_once_before_required_finish(self):
        _,inputs=self.build();calls=[]
        q=SimpleNamespace(pin=lambda name:(calls.append(name) or inputs[name]))
        with patch.object(f,'direct_file',return_value=None):f.verify_bytes(q,inputs)
        self.assertEqual(calls,list(inputs));self.assertEqual(len(calls),58)

    def test_new_input_inventory_does_not_modify_original_manifest_objects(self):
        before=copy.deepcopy((self.p77,self.form,self.note,self.native));self.build()
        self.assertEqual((self.p77,self.form,self.note,self.native),before)

    def test_final_fresh_pass_in_main_is_mandatory(self):
        import inspect
        source=inspect.getsource(f.main)
        self.assertIn('verify_bytes(q,inputs);q.finish()',source)
        self.assertIn('runtime_input_exclusions_authorized=False',source)


if __name__=='__main__':unittest.main()
