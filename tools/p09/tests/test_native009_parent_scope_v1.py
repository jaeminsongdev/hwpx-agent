import copy
import unittest
from types import SimpleNamespace

MODULE=None
API=None
HINT=None
WIRE=None
CHECKPOINT=None


class Tests(unittest.TestCase):
    def test_real_scope_rejects_conflicting_declaration(self):
        import current_stored_runtime_scope as scope
        pin=dict(path='tools/p09/fixed.py',bytes=1,sha256='a'*64)
        class Binding:
            originals={}
            def semantic_union(self,rows,checkpoint):raise AssertionError('must reject before original')
        binding=Binding();MODULE.inherit_declaration(SimpleNamespace(binding=binding),{pin['path']:pin},scope)
        with self.assertRaisesRegex(ValueError,'CONFLICT_NOT_SILENT_REBASE'):
            binding.semantic_union({pin['path']:dict(pin,bytes=2)},lambda:None)

    def test_preparation_union_keeps_original_and_complete_declaration(self):
        calls=[]
        class Binding:
            originals={'prior':{},'failed':{}}
            def semantic_union(self,rows,checkpoint):calls.append(rows);return rows,{'original':True}
        scope=SimpleNamespace(pins=lambda rows:{r['path']:r for r in rows},extend=lambda left,right:{**left,**right})
        inherited={'failed':{'path':'failed'}};binding=Binding()
        proof=MODULE.inherit_declaration(SimpleNamespace(binding=binding),inherited,scope)
        rows,result=binding.semantic_union({'prior':{'path':'prior'}},lambda:None)
        self.assertEqual(rows,{'prior':{'path':'prior'},**inherited});self.assertEqual(len(calls),1)
        self.assertEqual(result,{'original':True});self.assertEqual(proof['first_union_added_original_paths'],['failed'])
        self.assertFalse(proof['current_fresh_hashes_or_Frame_qualified'])

    def test_original_union_conflict_rejection_remains(self):
        class Binding:
            originals={}
            def semantic_union(self,rows,checkpoint):raise ValueError('ORIGINAL_REJECTION')
        scope=SimpleNamespace(pins=lambda rows:{r['path']:r for r in rows},extend=lambda left,right:{**left,**right})
        binding=Binding();MODULE.inherit_declaration(SimpleNamespace(binding=binding),{},scope)
        with self.assertRaisesRegex(ValueError,'ORIGINAL_REJECTION'):binding.semantic_union({},lambda:None)
        with self.assertRaises(ValueError):MODULE.inherit_declaration(SimpleNamespace(binding=binding),{},scope)

    def test_failed_original_is_read_and_validated_before_union(self):
        calls=[];pin={'path':'fixed-original'};row={'failed':True}
        q=SimpleNamespace(snapshots={})
        def read(reader,expected):
            self.assertIs(reader,q);self.assertEqual(expected,pin)
            reader.snapshots[pin['path']]=pin;calls.append('read');return row
        def validate(value):
            self.assertIs(value,row);self.assertEqual(q.snapshots[pin['path']],pin)
            calls.append('failed-state')
        self.assertIs(MODULE.admit_failed_declaration(q,SimpleNamespace(ORIGINAL=pin),
            SimpleNamespace(read_exact=read),SimpleNamespace(failed_state=validate)),row)
        self.assertEqual(calls,['read','failed-state'])

    def test_invalid_failed_original_is_not_admitted(self):
        def invalid(value):raise ValueError('FAIL_CLOSED')
        with self.assertRaisesRegex(ValueError,'FAIL_CLOSED'):
            MODULE.admit_failed_declaration(object(),SimpleNamespace(ORIGINAL={}),
                SimpleNamespace(read_exact=lambda q,p:{}),SimpleNamespace(failed_state=invalid))

    def test_v2_exact_capsule_path_and_run9_validate(self):
        self.assertEqual(API.validate(HINT)['run'],9)
        self.assertEqual(HINT['capsule_pin']['path'],MODULE.CAPSULE)

    def test_old_v1_not_silently_accepted_as_v2(self):
        hint=copy.deepcopy(HINT);hint['capsule_pin']['path']=hint['capsule_pin']['path'].replace('.v2.json','.v1.json')
        with self.assertRaises(ValueError):API.validate(hint)

    def test_old_run8_and_other_case_not_accepted(self):
        for key,value in (('run',8),('index',164)):
            hint=copy.deepcopy(HINT);hint[key]=value
            with self.assertRaises(ValueError):API.validate(hint)

    def test_original_reconstruction_retains_all69(self):
        graph,proof=API.reconstruct(HINT,WIRE,CHECKPOINT)
        self.assertEqual(len(graph.binding.descriptors()),69)
        self.assertTrue(proof['whole_original_reconstruction_code_retained'])

    def test_same_case_failed_execution_remains_unknown(self):
        self.assertIsNone(HINT['native008_failed_capture_declaration']['actual_failed_product_child_executed'])
        hint=copy.deepcopy(HINT);hint['native008_failed_capture_declaration']['actual_failed_product_child_executed']=False
        with self.assertRaises(ValueError):API.validate(hint)

    def test_original_transport_hash_still_rejects_changed_bytes(self):
        with self.assertRaises(ValueError):API.reconstruct(HINT,WIRE+b' ',CHECKPOINT)
