"""New eight-case namespace/saved-image/closed-input models; never starts Native."""
import contextlib,copy,inspect,io,json,sys,unittest
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import Mock,patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import prepared_bookmark_native755 as m
import prepared_bookmark_native690 as old
import run_prepared_bookmark_native755 as entry

ROOT=m.r.c.ROOT
def request(**kw):
    v=dict(schema_version=m.REQUEST,sequence=1,case_index=1,operation='checkpoint',step='prepare_slot');v.update(kw);return json.dumps(v)

class Contracts(unittest.TestCase):
    def test_all_eight_new_ordinals_only(self):
        self.assertEqual([m.directory(i)[-2:]for i in range(1,9)],[f'{i:02}'for i in range(1,9)])
        self.assertTrue(all('755-native001' in m.directory(i)for i in range(1,9)))
        for i in (True,0,9,1.0):
            with self.assertRaises(ValueError):m.directory(i)
    def test_all_sixteen_checkpoint_contracts_for_eight_cases(self):
        for i in range(1,9):
            for step in m.STEPS:
                _,internal=m.translate_request(request(case_index=i,step=step));self.assertEqual(internal['step'],m.LEGACY[step])
    def test_consumed_namespace_unknown_steps_and_caller_paths_rejected(self):
        for value in(request(schema_version=old.REQUEST),request(case_index=9),request(case_index=True),request(step='sdk_insert'),request(path='caller')):
            with self.assertRaises(ValueError):m.translate_request(value)
    def test_final_finish_is_eight_not_two(self):
        h=NS(guard=Mock());cases=NS(between=Mock(return_value=True));handler=m.Handler(h,cases)
        with patch.object(m.base.BatchHandler,'handle',return_value=json.dumps(dict(acknowledged=True))):
            handler.handle(json.dumps(dict(operation='finish',case_index=2,case_status='returned')));h.guard.advance.assert_not_called()
            handler.handle(json.dumps(dict(operation='finish',case_index=8,case_status='returned')))
        label,closed=h.guard.advance.call_args.args;self.assertEqual(label,'batch_close');self.assertTrue(closed());cases.between.assert_called_once_with(9)
    def test_failed_finish_does_not_advance(self):
        h=NS(guard=Mock());cases=NS();handler=m.Handler(h,cases)
        with patch.object(m.base.BatchHandler,'handle',return_value=json.dumps(dict(acknowledged=False))):handler.handle(json.dumps(dict(operation='finish',case_index=8,case_status='failed')))
        h.guard.advance.assert_not_called()
    def test_host_and_case_owner_guard_bodies_are_preserved(self):
        for name in('respond','close','summary'):
            self.assertEqual(inspect.getsource(getattr(m.Host,name)),inspect.getsource(getattr(old.Host,name)).replace('690','755'))
        self.assertEqual(inspect.getsource(m.Cases),inspect.getsource(old.Cases).replace('690','755'))
    def test_same_transport_and_retirement_implementation(self):
        self.assertIs(m.io,old.io);self.assertIs(m.drain,old.drain)
        records=m.drain.SessionRecords(8)
        for i in range(1,17):records.append(dict(process_id=i,process_birth_100ns=i*100,session_id=1,closed=True,observations=[]))
        with self.assertRaises(ValueError):records.append(dict(process_id=17,process_birth_100ns=1700,session_id=1,closed=True,observations=[]))
    def test_same_resource_deadlines_and_eight_sections(self):
        self.assertEqual((m.sections.SECTION_SECONDS,m.sections.WHOLE_SECONDS),(600,1800))
        self.assertEqual(m.sections.SECTIONS,('preparation','qualification',*('case'+str(i)for i in range(1,9)),'batch_close','final_audit'))
        expected=inspect.getsource(old.sections.guard_type).replace('690','755').replace('tail-two-closed','renamed-eight-closed')
        self.assertEqual(inspect.getsource(m.sections.guard_type),expected)
    def test_current_parser_cannot_replay_prior_commands(self):
        for args in([],['--execute-remaining-two-once'],['--execute-block-eight-once'],['--execute-renamed-eight-once','--retry'],['--execute-renamed-eight-once','--inspect-only']):
            with contextlib.redirect_stderr(io.StringIO()),self.assertRaises(SystemExit):entry.parser().parse_args(args)
        self.assertTrue(entry.parser().parse_args(['--execute-renamed-eight-once']).execute_renamed_eight_once)
    def test_captured_rows_use_all_eight_distinct_owner_pairs(self):
        reader=Mock();reader.snapshots={};reader.final_fresh_hashes=0;host=NS(scope=NS(sessions=list(range(16))))
        with patch.object(m.evidence.r.a,'AcceptanceReader',return_value=reader),patch.object(m.evidence,'captured',side_effect=lambda q,f,i,p:(i,p)):
            value=m.evidence.current_artifacts(Mock(),host,m.directory)
        self.assertEqual(value['cases'],[(i,[2*(i-1),2*(i-1)+1])for i in range(1,9)])
    def trace(self):
        artifacts={name:dict(pin=dict(bytes=1,sha256='a'*64),owner=0 if not name.startswith('reopened')else 1,effect_semantics_qualified=False)for name in('initial.hwpx','saved.hwpx','reopened.hwpx')}
        for role in('initial','saved','reopened'):
            artifacts[role+'-page-001.bmp']=dict(pin=dict(bytes=54,sha256='b'*64),owner=0 if role!='reopened'else 1,
                page_number=0,page_count=1,bitmap=dict(format='BMP',depth=24,resolution=96,visual_semantics_qualified=False),effect_semantics_qualified=False)
        return dict(schema_version='hwpx-agent.private.prepared-bookmark755-trace/v1',case_index=1,source_case_index=1,
            state='capture_returned_semantics_unqualified',error_code=None,cleanup_error=None,source_identity_preserved=True,
            input_leases_closed=True,SDK_insertion_invoked=False,sessions=[dict(process=0),dict(process=1)],artifacts=artifacts)
    def capture(self,trace):
        reader=Mock();reader.json.return_value=trace
        def pin(path):return dict(path=path,**trace['artifacts'].get(path.rsplit('/',1)[-1],{}).get('pin',dict(bytes=1,sha256='c'*64)))
        reader.pin.side_effect=pin
        with patch.object(m.evidence,'producer'):return m.evidence.captured(reader,'fixed-folder',1,[])
    def test_three_complete_roles_bind_to_correct_save_and_reopen_owner(self):
        value=self.capture(self.trace());self.assertEqual(value['source_case_index'],1)
        self.assertTrue(value['native_capture_bound']);self.assertFalse(value['reference_semantics_qualified'])
    def test_missing_saved_image_is_not_a_complete_capture(self):
        t=self.trace();del t['artifacts']['saved-page-001.bmp']
        with self.assertRaisesRegex(ValueError,'ALL_RENDERED_PAGES_BOUND'):self.capture(t)
    def test_saved_image_cannot_claim_reopen_owner(self):
        t=self.trace();t['artifacts']['saved-page-001.bmp']['owner']=1
        with self.assertRaisesRegex(ValueError,'IMMUTABLE_ARTIFACT_AND_PRODUCER'):self.capture(t)
    def test_missing_page_noncontiguous_page_and_extra_artifact_rejected(self):
        for mutation in('count','index','extra'):
            t=self.trace()
            if mutation=='count':t['artifacts']['saved-page-001.bmp']['page_count']=2
            elif mutation=='index':t['artifacts']['saved-page-001.bmp']['page_number']=1
            else:t['artifacts']['caller.hwpx']=copy.deepcopy(t['artifacts']['saved.hwpx'])
            with self.assertRaises(ValueError):self.capture(t)
    def test_old_saved_absence_or_tail_mapping_is_not_new_evidence(self):
        t=self.trace();t['source_case_index']=7
        with self.assertRaises(ValueError):self.capture(t)
    def test_ports_change_only_saved_role_and_paired_saved_observation(self):
        expected=(ROOT/old.PORTS).read_text(encoding='utf-8').replace('690','755').replace("@('initial','reopened')","@('initial','saved','reopened')")
        marker="                Open-P09Prepared755Lease $State (Join-Path $State.run 'saved.hwpx') $State.saved.sha256\n"
        expected=expected.replace(marker,marker+"                Export-P09Prepared755Pages $State saved\n                Observe-P09Prepared755Document $State (Join-Path $State.run 'saved.hwpx') $State.saved.sha256\n")
        self.assertEqual((ROOT/m.PORTS).read_text(encoding='utf-8'),expected)
    def test_channel_is_only_namespace_projection(self):
        self.assertEqual((ROOT/m.CHANNEL).read_text(encoding='utf-8'),(ROOT/old.CHANNEL).read_text(encoding='utf-8').replace('690','755'))
    def test_manifest_binds_exact_current_renamed_files(self):
        value=json.loads((ROOT/m.prepared.PREPARED).read_text(encoding='utf-8'));nav=json.loads((ROOT/m.prepared.PINS).read_text(encoding='utf-8'))
        self.assertEqual([c['output']for c in value['cases']],[c['renamed']for c in nav['cases']]);self.assertEqual(len(value['cases']),8)
        self.assertFalse(value['native_execution_authorized']);self.assertFalse(value['P09_complete'])
    def test_no_consumed_code_or_claim_namespace(self):
        self.assertIn('760-code001',entry.CODE);self.assertIn('755-claim001',entry.CLAIM);self.assertIn('755-native001',entry.OUTPUT)
        self.assertNotEqual(entry.OUTPUT,old.ENTRY);self.assertFalse((ROOT/entry.OUTPUT).exists());self.assertFalse((ROOT/entry.CLAIM).exists())
    def test_fixed_worker_cannot_select_only_two_or_old_source_candidates(self):
        text=(ROOT/m.TARGET).read_text(encoding='utf-8')
        for expected in('PreparedRenamedEightAfterCurrentSession','planned_cases=8','$completed -eq 8','bookmark-rename740-generated001/case-'):
            self.assertIn(expected,text)
        self.assertNotIn('Select-Object -Skip 6',text);self.assertNotIn('GetActiveObject',text);self.assertNotIn('New-Object -ComObject',text)
    def test_entry_cannot_claim_semantic_acceptance(self):
        text=(ROOT/entry.SELF).read_text(encoding='utf-8')
        self.assertIn('reference_semantics_qualified=False',text);self.assertIn('accepted_count_delta=0',text);self.assertIn('automatic_retry=False',text)

if __name__=='__main__':
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(Contracts);out=io.StringIO();result=unittest.TextTestRunner(stream=out,verbosity=0).run(suite)
    print(json.dumps(dict(run=result.testsRun,errors=len(result.errors),failures=len(result.failures),skipped=len(result.skipped),actual_native_started=False,
        failed_test_ids=[t.id().rsplit('.',1)[-1]for t,_ in result.errors+result.failures])))
    raise SystemExit(0 if result.wasSuccessful()else 2)
