"""Ten new fixed-plan controls; metadata/code only, no Native activation."""
import copy
import json
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import block_bookmark_source_plan643 as m
import run_prepared_bookmark_native631 as p

ROOT=Path(__file__).resolve().parents[3]
RECEIPT='implementation/p09/evidence/p09-361-block-bookmark-typelib642-inspection001.v1.json'

class Tests(unittest.TestCase):
    def setUp(self):
        self.value=p.codec.unpack(json.loads((ROOT/RECEIPT).read_text(encoding='utf-8')))['declarations']
        self.plan=m.build(self.value)
    def denied(self,change):
        value=copy.deepcopy(self.plan);change(value)
        with self.assertRaises(ValueError):m.validate(value,self.value)
    def test_exact_one_document_eight_ranges(self):
        self.assertTrue(m.validate(self.plan,self.value));self.assertEqual(self.plan['whole_seed_text'].count('\r\n'),7)
    def test_no_native_entry_or_permit(self):
        self.assertFalse(self.plan['native_execution_authorized']);self.assertFalse(self.plan['native_entry_implemented'])
        self.denied(lambda p:p.update(native_execution_authorized=True))
    def test_arbitrary_path_rejected(self):self.denied(lambda p:p.update(output_directory='C:/outside'))
    def test_changed_target_name_rejected(self):self.denied(lambda p:p['cases'][0].update(bookmark_name='caller'))
    def test_empty_range_rejected(self):self.denied(lambda p:p['cases'][0]['selection'].update(epos=0))
    def test_bool_not_native_coordinate(self):self.denied(lambda p:p['cases'][0]['selection'].update(spos=False))
    def test_wrong_seed_or_bookmark_type_rejected(self):
        self.denied(lambda p:p['cases'][0].update(seed_text='caller'));self.denied(lambda p:p['SDK_Bookmark'].update(block_type_value=0))
    def test_caller_block_flag_rejected(self):self.denied(lambda p:p.update(block=True))
    def test_changed_native_member_or_extra_shortcut_rejected(self):
        value=copy.deepcopy(self.value)
        next(t for t in value['selected_types']if t['name']=='HBookMark')['members'].append(dict(name='Type',invoke_kind='INVOKE_PROPERTYPUT',return_variant_type=24,parameters=[dict(variant_type=19,flags=1)]))
        with self.assertRaises(ValueError):m.build(value)
    def test_wrong_action_variant_signature_rejected(self):
        value=copy.deepcopy(self.value)
        member=next(x for t in value['selected_types']if t['name']=='HAction'for x in t['members']if x['name']=='Execute')
        member['return_variant_type']=3
        with self.assertRaises(ValueError):m.build(value)

if __name__=='__main__':
    result=unittest.TestResult();unittest.defaultTestLoader.loadTestsFromTestCase(Tests).run(result)
    print(json.dumps(dict(run=result.testsRun,errors=len(result.errors),failures=len(result.failures),skipped=len(result.skipped))))
    raise SystemExit(0 if result.wasSuccessful()else 2)
