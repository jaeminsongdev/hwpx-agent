"""New text-read diagnostics and entry integration; no Native calls or old test replay."""
import copy,hashlib,inspect,io,json,sys,unittest
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import Mock,patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import prepared_bookmark_native773 as m
import prepared_bookmark_native768 as old
import run_prepared_bookmark_native773 as e
ROOT=m.r.c.ROOT
class Reader:
    def __init__(self):self.root=ROOT;self.snapshots={};self.checkpoint=lambda:None
    def pin(self,name):
        b=(ROOT/name).read_bytes();p=dict(path=name,bytes=len(b),sha256=hashlib.sha256(b).hexdigest());self.snapshots[name]=p;return p
    def json(self,name):self.pin(name);return json.loads((ROOT/name).read_text(encoding='utf-8'))
class Checks(unittest.TestCase):
    def trace(self):
        manifest=json.loads((ROOT/m.prepared.PREPARED).read_text());case=manifest['cases'][0];rows=[]
        for stage,pin in(('initial',case['output']),('reopened',case['reopened'])):
            name=manifest['target_name_sha256'];selected=manifest['target_content_sha256'];whole='c'*64
            readings=[dict(role=role,option_mode='selected_block'if role=='selected'else'whole_document',returned=True,result_kind='string',utf16_characters=10 if role=='selected'else 30,UTF8_bytes=10 if role=='selected'else 35,sha256=selected if role=='selected'else whole,exception_kind=None,hresult=None)for role in('before','selected','after')]
            rows.append(dict(stage=stage,source_sha256=pin['sha256'],complete=True,bookmark_command=1,target_name_sha256=name,selected_text_sha256=selected,selected_UTF8_bytes=10,selected_characters=10,origin=[0,0,16],selection_positions=[0,0,19,0,0,29],confirmation_selection_positions=[0,0,19,0,0,29],whole_text_before_sha256=whole,whole_text_after_sha256=whole,source_bytes_rewritten=False,hyperlink_activation_invoked=False,text_reads=readings))
        return dict(schema_version='hwpx-agent.private.prepared-bookmark773-trace/v1',case_index=1,source_case_index=1,state='capture_returned_semantics_unqualified',error_code=None,cleanup_error=None,source_identity_preserved=True,input_leases_closed=True,SaveAs_invoked=False,direct_bookmark_cursor_only=True,SDK_insertion_invoked=False,artifacts={},navigation=rows)
    def capture(self,t):
        q=Reader();read=q.json;pin=q.pin;q.json=lambda name:t if name.endswith('case-trace.json')else read(name)
        q.pin=lambda name:dict(path=name,bytes=1,sha256='d'*64)if name.endswith('case-trace.json')else pin(name)
        with patch.object(m.evidence,'producer'):return m.evidence.captured(q,'fixed',1,[])
    def test_actual_existing_input_pairs_and_product_XZ_are_bound(self):
        v=m.prepared.validate_prepared(Reader());self.assertEqual(len(v['cases']),8);self.assertFalse(v['SaveAs_invoked'])
    def test_owner_resource_protocol_implementations_are_namespace_only(self):
        for name in('respond','close','summary'):self.assertEqual(inspect.getsource(getattr(m.Host,name)),inspect.getsource(getattr(old.Host,name)).replace('768','773'))
        self.assertEqual(inspect.getsource(m.Cases),inspect.getsource(old.Cases).replace('768','773'))
        self.assertEqual(inspect.getsource(m.sections.guard_type),inspect.getsource(old.sections.guard_type).replace('768','773'))
        self.assertIs(m.io,old.io);self.assertIs(m.drain,old.drain)
    def test_success_requires_all_three_explicit_return_records(self):
        value=self.capture(self.trace());self.assertEqual(len(value['direct_bookmark_cursor_observations']),2);self.assertFalse(value['hyperlink_activation_qualified'])
    def test_old_or_wrong_option_role_is_not_accepted_as_full_document(self):
        for role in('selected_block','saveblock:false'):
            t=self.trace();t['navigation'][0]['text_reads'][0]['option_mode']=role
            with self.assertRaises(ValueError):self.capture(t)
    def test_empty_wrong_type_short_whole_and_boolean_length_are_rejected(self):
        for key,value in(('result_kind','null'),('returned',False),('utf16_characters',0),('utf16_characters',10),('utf16_characters',True)):
            t=self.trace();t['navigation'][0]['text_reads'][0][key]=value
            with self.assertRaises(ValueError):self.capture(t)
    def test_mismatched_hash_missing_read_or_extra_fallback_read_is_rejected(self):
        for kind in('hash','missing','extra'):
            t=self.trace();reads=t['navigation'][0]['text_reads']
            if kind=='hash':reads[1]['sha256']='0'*64
            elif kind=='missing':reads.pop()
            else:reads.append(copy.deepcopy(reads[-1]))
            with self.assertRaises(ValueError):self.capture(t)
    def test_entry_reads_actual_xz_format_and_keeps_source_drift_rejection(self):
        v=e.codec.unpack(json.loads((ROOT/'implementation/p09/evidence/p09-361-bookmark-cursor772-code001.v1.json').read_text()),lambda:None)
        v={k:v[k]for k in('state','cleanup','fresh_inputs','final_fresh_hashes','all_new_tests_passed','actual_native_started','ready_denial','execution_dependency_paths','source_pins')};v['state']=e.STATE
        paths=set(v['execution_dependency_paths'])|m.SOURCES|m.prepared.loaded_dependencies(ROOT);v['execution_dependency_paths']=sorted(paths)
        pins={name:dict(path=name,bytes=1,sha256='a'*64)for name in paths};v['source_pins']=list(pins.values())
        q=NS(json=Mock(return_value=e.codec.pack(v,lambda:None)),pin=Mock(side_effect=lambda name:pins[name]),checkpoint=Mock());e.load_code(q)
        self.assertTrue(q.checkpoint.called);q.pin.side_effect=lambda name:dict(path=name,bytes=0,sha256='0'*64)
        with self.assertRaises(ValueError):e.load_code(q)
    def test_source_read_uses_only_default_whole_and_canonical_selected_options(self):
        text=(ROOT/'implementation/p09/tools/bookmark-target-cursor773.ps1').read_text(encoding='utf-8')
        self.assertIn("$option=if ($Role -ceq 'selected') {'saveblock'} else {''}",text)
        self.assertEqual(text.count(".GetTextFile('TEXT',$option)"),1)
        self.assertNotIn(".GetTextFile('TEXT','saveblock:false')",text);self.assertNotIn('.SaveAs(',text)
        for path in(e.OUTPUT,e.CLAIM,e.SCRATCH):self.assertFalse((ROOT/path).exists())
if __name__=='__main__':
    out=io.StringIO();result=unittest.TextTestRunner(stream=out,verbosity=0).run(unittest.defaultTestLoader.loadTestsFromTestCase(Checks))
    print(json.dumps(dict(run=result.testsRun,errors=len(result.errors),failures=len(result.failures),skipped=len(result.skipped),actual_native_started=False,failed_test_ids=[t.id().rsplit('.',1)[-1]for t,_ in result.errors+result.failures])))
    raise SystemExit(0 if result.wasSuccessful()else 2)
