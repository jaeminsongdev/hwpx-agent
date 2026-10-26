"""New query-only cursor/purpose/source/envelope models, never Native activation."""
import contextlib,copy,inspect,io,json,hashlib,sys,unittest
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import Mock,patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import prepared_bookmark_native768 as m
import prepared_bookmark_native755 as old
import run_prepared_bookmark_native768 as entry
import run_prepared_bookmark_native761 as consumed
ROOT=m.r.c.ROOT
class Reader:
    def __init__(self):self.root=ROOT;self.snapshots={};self.checkpoint=lambda:None
    def pin(self,name):
        data=(self.root/name).read_bytes();pin=dict(path=name,bytes=len(data),sha256=hashlib.sha256(data).hexdigest());self.snapshots[name]=pin;return pin
    def json(self,name):self.pin(name);return json.loads((self.root/name).read_text(encoding='utf-8'))

class Contracts(unittest.TestCase):
    def test_current_preparation_reads_actual_XZ_product_proof_without_legacy_callback(self):
        value=m.prepared.validate_prepared(Reader());self.assertEqual(len(value['cases']),8);self.assertFalse(value['SaveAs_invoked']);self.assertFalse(value['hyperlink_activation_qualified'])
    def test_manifest_uses_original_native_pairs_not_new_saves_or_old_renamed_candidates(self):
        v=json.loads((ROOT/m.prepared.PREPARED).read_text());self.assertEqual([c['case_index']for c in v['cases']],list(range(1,9)))
        for c in v['cases']:
            self.assertTrue(c['output']['path'].endswith('/initial.hwpx'));self.assertTrue(c['reopened']['path'].endswith('/reopened.hwpx'))
    def test_old_request_and_caller_path_or_unsupported_steps_are_rejected(self):
        base=dict(schema_version=m.REQUEST,sequence=1,case_index=1,operation='checkpoint',step='prepare_slot')
        for change in(dict(schema_version=old.REQUEST),dict(path='caller'),dict(step='SaveAs'),dict(case_index=True),dict(case_index=9)):
            with self.assertRaises(ValueError):m.translate_request(json.dumps(dict(base,**change)))
    def test_all_sixteen_fixed_checkpoints_are_preserved_for_eight_queries(self):
        for i in range(1,9):
            for step in m.STEPS:
                _,v=m.translate_request(json.dumps(dict(schema_version=m.REQUEST,sequence=1,case_index=i,operation='checkpoint',step=step)))
                self.assertEqual(v['step'],m.LEGACY[step])
    def test_host_owner_and_lifecycle_bodies_are_namespace_only(self):
        for name in('respond','close','summary'):self.assertEqual(inspect.getsource(getattr(m.Host,name)),inspect.getsource(getattr(old.Host,name)).replace('755','768'))
        self.assertEqual(inspect.getsource(m.Cases),inspect.getsource(old.Cases).replace('755','768'))
        self.assertIs(m.io,old.io);self.assertIs(m.drain,old.drain)
    def test_resource_sections_and_deadlines_unchanged(self):
        self.assertEqual(inspect.getsource(m.sections.guard_type),inspect.getsource(old.sections.guard_type).replace('755','768'))
        self.assertEqual((m.sections.SECTION_SECONDS,m.sections.WHOLE_SECONDS),(600,1800));self.assertEqual(len(m.sections.SECTIONS),12)
    def test_worker_namespace_and_exclusive_output_are_new(self):
        self.assertNotEqual(entry.OUTPUT,consumed.OUTPUT)
        for path in(entry.OUTPUT,entry.CLAIM,entry.SCRATCH):self.assertFalse((ROOT/path).exists())
        for i in range(1,9):self.assertFalse((ROOT/m.directory(i)).exists())
    def test_previous_execution_flags_and_retry_are_rejected(self):
        for args in([],['--execute-renamed-eight-once'],['--execute-bookmark-cursor-eight-once','--retry']):
            with contextlib.redirect_stderr(io.StringIO()),self.assertRaises(SystemExit):entry.parser().parse_args(args)
        self.assertTrue(entry.parser().parse_args(['--execute-bookmark-cursor-eight-once']).execute_bookmark_cursor_eight_once)
    def trace(self):
        manifest=json.loads((ROOT/m.prepared.PREPARED).read_text());c=manifest['cases'][0];rows=[]
        for label,pin in(('initial',c['output']),('reopened',c['reopened'])):
            rows.append(dict(stage=label,source_sha256=pin['sha256'],complete=True,bookmark_command=1,target_name_sha256=manifest['target_name_sha256'],selected_text_sha256=manifest['target_content_sha256'],selected_UTF8_bytes=10,selected_characters=10,whole_text_before_sha256='c'*64,whole_text_after_sha256='c'*64,origin=[0,0,16],selection_positions=[0,0,19,0,0,29],confirmation_selection_positions=[0,0,19,0,0,29],source_bytes_rewritten=False,hyperlink_activation_invoked=False))
        return dict(schema_version='hwpx-agent.private.prepared-bookmark768-trace/v1',case_index=1,source_case_index=1,state='capture_returned_semantics_unqualified',error_code=None,cleanup_error=None,source_identity_preserved=True,input_leases_closed=True,SaveAs_invoked=False,direct_bookmark_cursor_only=True,SDK_insertion_invoked=False,artifacts={},navigation=rows)
    def capture(self,t):
        q=Reader();read=q.json
        def value(name):return t if name.endswith('/case-trace.json')else read(name)
        q.json=value;pin=q.pin;q.pin=lambda name:dict(path=name,bytes=1,sha256='d'*64)if name.endswith('/case-trace.json')else pin(name)
        with patch.object(m.evidence,'producer'):return m.evidence.captured(q,'fixed',1,[])
    def test_current_pair_trace_binds_two_sources_and_exact_native_selection(self):
        v=self.capture(self.trace());self.assertEqual(len(v['direct_bookmark_cursor_observations']),2);self.assertFalse(v['hyperlink_activation_qualified']);self.assertFalse(v['P09_complete'])
    def test_wrong_name_source_text_or_source_file_cannot_qualify(self):
        for key in('target_name_sha256','selected_text_sha256','source_sha256'):
            t=self.trace();t['navigation'][0][key]='0'*64
            with self.assertRaises(ValueError):self.capture(t)
    def test_six_typed_positions_and_confirmation_are_required(self):
        for key,value in(('selection_positions',[0,0,19,0,0,30]),('confirmation_selection_positions',[False,0,19,0,0,29]),('origin',[0,1,16])):
            t=self.trace();t['navigation'][0][key]=value
            with self.assertRaises(ValueError):self.capture(t)
    def test_saved_or_activated_link_or_changed_body_is_not_cursor_query_success(self):
        for key in('SaveAs_invoked','SDK_insertion_invoked'):
            t=self.trace();t[key]=True
            with self.assertRaises(ValueError):self.capture(t)
        for key,value in(('hyperlink_activation_invoked',True),('whole_text_after_sha256','b'*64),('bookmark_command',True),('complete',False)):
            t=self.trace();t['navigation'][0][key]=value
            with self.assertRaises(ValueError):self.capture(t)
    def test_missing_query_or_old_trace_schema_is_rejected(self):
        for t in(self.trace(),self.trace()):
            if len(t['navigation'])==2:t['navigation'].pop()
            with self.assertRaises(ValueError):self.capture(t)
        t=self.trace();t['schema_version']='hwpx-agent.private.prepared-bookmark755-trace/v1'
        with self.assertRaises(ValueError):self.capture(t)
    def test_new_entry_uses_current_XZ_reader_and_enforces_full_status_and_closure(self):
        prior=entry.codec.unpack(json.loads((ROOT/consumed.CODE).read_text()),lambda:None)
        prior={k:prior[k]for k in('state','cleanup','fresh_inputs','final_fresh_hashes','all_new_tests_passed','actual_native_started','ready_denial','execution_dependency_paths','source_pins')}
        prior['state']=entry.STATE;paths=set(prior['execution_dependency_paths'])|m.SOURCES|m.prepared.loaded_dependencies(ROOT);prior['execution_dependency_paths']=sorted(paths)
        pins={name:dict(path=name,bytes=1,sha256='a'*64)for name in paths};prior['source_pins']=list(pins.values())
        q=NS(json=Mock(return_value=entry.codec.pack(prior,lambda:None)),pin=Mock(side_effect=lambda name:pins[name]),checkpoint=Mock())
        entry.load_code(q);self.assertTrue(q.checkpoint.called)
        for mutate in('legacy','status','source'):
            q.pin.side_effect=lambda name:pins[name];v=copy.deepcopy(prior)
            if mutate=='status':v['cleanup']=False
            if mutate=='source':q.pin.side_effect=lambda name:dict(path=name,bytes=0,sha256='0'*64)
            q.json.return_value=entry.publisher.codec.pack(v)if mutate=='legacy'else entry.codec.pack(v,lambda:None)
            with self.assertRaises(ValueError):entry.load_code(q)
    def test_worker_manifest_hash_and_no_save_calls_are_fixed(self):
        worker=(ROOT/m.TARGET).read_text(encoding='utf-8');ports=(ROOT/m.PORTS).read_text(encoding='utf-8')
        self.assertIn(hashlib.sha256((ROOT/m.prepared.PREPARED).read_bytes()).hexdigest(),worker);self.assertIn('PreparedBookmarkCursorEightAfterCurrentSession',worker)
        self.assertNotIn('.SaveAs(',ports);self.assertNotIn('CreatePageImage(',ports);self.assertIn('Invoke-P09BookmarkCursor768',ports)

if __name__=='__main__':
    out=io.StringIO();result=unittest.TextTestRunner(stream=out,verbosity=0).run(unittest.defaultTestLoader.loadTestsFromTestCase(Contracts))
    print(json.dumps(dict(run=result.testsRun,errors=len(result.errors),failures=len(result.failures),skipped=len(result.skipped),actual_native_started=False,failed_test_ids=[t.id().rsplit('.',1)[-1]for t,_ in result.errors+result.failures])))
    raise SystemExit(0 if result.wasSuccessful()else 2)
