"""Changed eight-case boundaries and full transport, without any Native process."""
import contextlib,copy,inspect,io,json,sys,unittest
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import Mock,patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import prepared_bookmark_native684 as m
import prepared_bookmark_native631 as old
import prepared_bookmark684_io as transport
import crossref_native_worker_io603 as oldio
import prepared_bookmark684_notice as notice
import run_prepared_bookmark_native684 as entry
import prepared_bookmark684_receipt as codec

def frame(**kw):
    row=dict(schema_version=m.REQUEST,sequence=1,case_index=1,operation='checkpoint',step='prepare_slot');row.update(kw);return json.dumps(row)

class Contracts(unittest.TestCase):
    def test_01_exact_eight_and_no_tail_mapping(self):
        self.assertEqual([m.directory(i)[-2:]for i in range(1,9)],[f'{i:02}'for i in range(1,9)])
        for i in(True,0,9):
            with self.assertRaises(ValueError):m.directory(i)
    def test_02_each_case_each_step_exact(self):
        for index in range(1,9):
            for step in m.STEPS:
                public,internal=m.translate_request(frame(case_index=index,step=step))
                self.assertEqual(internal['case_index'],index);self.assertEqual(internal['step'],m.LEGACY[public['step']])
    def test_03_wire_denies_wrong_schema_type_and_unknown_operation(self):
        for raw in(frame(schema_version=old.REQUEST),frame(case_index=True),frame(case_index=9),frame(step='sdk_insert'),frame(path='caller'),frame()+'\n',frame()[:-1]+',"sequence":1}'):
            with self.assertRaises(ValueError):m.translate_request(raw)
    def test_04_same_host_lifecycle_and_guard_calls(self):
        for name in('respond','close','summary'):
            self.assertEqual(inspect.getsource(getattr(m.Host,name)),inspect.getsource(getattr(old.Host,name)).replace('631','684'))
        self.assertEqual(inspect.getsource(m.Cases),inspect.getsource(old.Cases).replace('631','684'))
    def test_05_finish_eight_only_advances_after_closed_owners(self):
        guard=Mock();host=NS(guard=guard);handler=m.Handler(host,NS(between=Mock(return_value=True)))
        with patch.object(m.base.BatchHandler,'handle',return_value=json.dumps(dict(acknowledged=True))):
            for index in(6,7):handler.handle(json.dumps(dict(operation='finish',case_index=index,case_status='returned')))
            guard.advance.assert_not_called()
            handler.handle(json.dumps(dict(operation='finish',case_index=8,case_status='returned')))
            label,closed=guard.advance.call_args.args;self.assertEqual(label,'batch_close');self.assertTrue(closed());handler.cases.between.assert_called_once_with(9)
    def test_06_failed_eighth_finish_cannot_advance(self):
        host=NS(guard=Mock());handler=m.Handler(host,Mock())
        with patch.object(m.base.BatchHandler,'handle',return_value=json.dumps(dict(acknowledged=False))):handler.handle(json.dumps(dict(operation='finish',case_index=8,case_status='failed')))
        host.guard.advance.assert_not_called()
    def test_07_six_or_uncertain_sessions_cannot_be_whole_eight(self):
        for count,cursor,stopped in((12,7,False),(16,9,True),(15,9,False)):
            host=NS(scope=NS(sessions=[None]*count),protocol=NS(protocol=NS(case_index=cursor,stopped=stopped)))
            with patch.object(m.evidence,'current_artifacts')as artifact,self.assertRaises(ValueError):m.artifacts(Mock(),host)
            artifact.assert_not_called()
    def test_08_original_limits_with_eight_closed_sections(self):
        source=(m.r.c.ROOT/'tools/p09/prepared_bookmark631_sections.py').read_text()
        current=(m.r.c.ROOT/'tools/p09/prepared_bookmark684_sections.py').read_text()
        self.assertEqual(current,source.replace('631','684').replace('range(1,7)','range(1,9)').replace('six-closed','eight-closed'))
        self.assertEqual((m.sections.SECTION_SECONDS,m.sections.WHOLE_SECONDS),(600,1800))
    def test_09_ports_preserve_save_identity_BMP_and_no_force_kill(self):
        root=m.r.c.ROOT;source=(root/old.PORTS).read_text();current=(root/m.PORTS).read_text()
        self.assertEqual(current,source.replace('631','684').replace('64539a2dc6e76f0301c8beba20cf24083810fdf571f1f5dabbbf2764cd1ee184',m.prepared.SOURCE_PIN['sha256']))
        self.assertEqual((root/m.CHANNEL).read_text(),(root/old.CHANNEL).read_text().replace('631','684'))
    def test_10_worker_whole_eight_exact_input_projection(self):
        root=m.r.c.ROOT;source=(root/old.TARGET).read_text()
        expected=source.replace('631','684').replace('PreparedRemainingSixAfterCurrentSession','PreparedBlockEightAfterCurrentSession').replace('p09-361-stored-bookmark-insertion628-prepared-batch','p09-361-block-bookmark681-prepared-batch')
        expected=expected.replace('af28cc0b005b10f5625ec912eba51c23b6ce6eb2941e387ea719529ec92d0306',m.prepared.MANIFEST_SHA).replace('PREPARED_EXACT_628_MANIFEST','PREPARED_EXACT_681_MANIFEST')
        expected=expected.replace('$manifest.cases | Select-Object -Skip 2','$manifest.cases').replace('$sourceIndex=$index+2','$sourceIndex=$index').replace('p09-361-bookmark-insertion628-prepared-001',Path(m.prepared.DIRECTORY).name)
        # Replacement above substitutes the original complete directory basename.
        expected=expected.replace('implementation/p09/evidence/private/p09-361-crossref-discovery-inputs-20261017-r01/source-with-bookmark.hwpx',m.prepared.SOURCE_PIN['path'])
        expected=expected.replace('$completed -eq 6','$completed -eq 8').replace('planned_cases=6','planned_cases=8').replace('remaining_six_callbacks','block_eight_callbacks')
        self.assertEqual((root/m.TARGET).read_text(),expected)
    def test_11_transport_keeps_original_cleanup_guard_and_thread_bodies(self):
        source=(m.r.c.ROOT/'tools/p09/crossref_native_worker_io603.py').read_text()
        expected=source.replace('from crossref_native_worker_io import result_notice,wait_native_exit','from crossref_native_worker_io import wait_native_exit\nfrom prepared_bookmark684_notice import result_notice')
        expected=expected.replace("SELF='tools/p09/crossref_native_worker_io603.py'","SELF='tools/p09/prepared_bookmark684_io.py'")
        expected=expected.replace('                for _ in range(160):','                # Eight cases: READY + 8*(16 checkpoints+2 admissions+2 closes+finish)\n                # + RESULT = 170 frames, then one bounded EOF read.\n                for _ in range(171):').replace("counts['stdout_bytes']>32768","counts['stdout_bytes']>65536")
        self.assertEqual((m.r.c.ROOT/'tools/p09/prepared_bookmark684_io.py').read_text(),expected)
    def transport_fixture(self,lines):
        g=NS(check=Mock(),windows=Mock(),samples=[dict(system_cpu_percent=1.,available_ram_percent=50.)])
        worker=NS(profile=dict(cleanup_confirmed=False),stdout=io.StringIO(lines),stderr=io.StringIO(''),stdin=io.StringIO(),process=None,returncode=0)
        worker.observe=Mock(return_value=dict(peak_job_private_percent=0));worker.signal_readonly_target=Mock();worker.wait=Mock();worker.poll=Mock(return_value=0)
        worker.close=lambda:worker.profile.update(cleanup_confirmed=True)
        handler=NS(handle=Mock(return_value='{}'),current_native=lambda:None,summary=lambda:{},close=lambda:None)
        return g,worker,handler
    def test_12_actual_in_memory170_frames_reach_result(self):
        schema='hwpx-agent.private.crossref-fixed-worker-result/v1'
        result=dict(schema_version=schema,state='block_eight_callbacks_returned_semantics_unqualified',phase='fixed_eight',retained_live_or_uncertain_owners=0)
        g,w,h=self.transport_fixture(('{}\n'*169)+json.dumps(result)+'\n');record={}
        value=transport.run(g,w,None,lambda *a,**kw:None,h,schema,{},lambda v:None,record)
        self.assertEqual(value,result);self.assertEqual(record['requests'],169);self.assertTrue(record['cleanup'])
    def test_13_actual_transport_rejects_oversize_frame(self):
        g,w,h=self.transport_fixture('x'*4097+'\n');record={}
        with self.assertRaises(ValueError):transport.run(g,w,None,lambda *a,**kw:None,h,'result',{},lambda v:None,record)
        h.handle.assert_not_called()
    def test_14_failed_and_success_notice_and_private_values(self):
        for state,failed in(('block_eight_callbacks_failed_or_partial',True),('block_eight_callbacks_returned_semantics_unqualified',False),('unknown',True)):
            value=notice.result_notice(dict(state=state,phase='fixed_eight',error_code='PRIVATE VALUE',case_failure=dict(case_index=8,phase='candidate_bind',error_code='PRIVATE VALUE')))
            self.assertIs(value['worker_failed_or_uncertain'],failed);self.assertEqual(value['failed_case_phase'],'candidate_bind');self.assertNotIn('PRIVATE VALUE',json.dumps(value))
    def test_15_no_old_retry_or_ambiguous_flags(self):
        for args in([],['--execute-remaining-six-once'],['--execute-block-eight-once','--retry'],['--execute-block-eight-once','--inspect-only']):
            with contextlib.redirect_stderr(io.StringIO()),self.assertRaises(SystemExit):entry.parser().parse_args(args)
        self.assertTrue(entry.parser().parse_args(['--execute-block-eight-once']).execute_block_eight_once)
    def test_16_codec_complete_roundtrip_and_integrity(self):
        row=dict(state='MODELED_NOT_NATIVE',data=[dict(index=i,digest=f'{i:064x}',preserved=True)for i in range(2000)])
        packet=codec.pack(row,lambda:None);self.assertEqual(codec.unpack(packet,lambda:None),row)
        bad=copy.deepcopy(packet);bad['payload_sha256']='0'*64
        with self.assertRaises(ValueError):codec.unpack(bad,lambda:None)
    def test_17_incomplete_producers_cannot_be_accepted(self):
        with self.assertRaises(ValueError):m.evidence.producer(dict(sessions=[],dual_identity_evidence=[]),[])
    def test_18_artifact_index_maps_all_eight(self):
        reader=Mock();reader.snapshots={};reader.final_fresh_hashes=0
        host=NS(scope=NS(sessions=list(range(16))))
        with patch.object(m.evidence.r.a,'AcceptanceReader',return_value=reader),patch.object(m.evidence,'captured',side_effect=lambda q,f,i,p:(i,p)):
            value=m.evidence.current_artifacts(Mock(),host,m.directory)
        self.assertEqual(value['cases'],[(i,[2*i-2,2*i-1])for i in range(1,9)])
    def test_19_exact_worker_command_unique_new_switch(self):
        reader=Mock();reader.root=m.r.c.ROOT;reader.snapshots={m.base.candidate.original.BOOTSTRAP:dict(sha256=m.base.candidate.original.BOOTSTRAP_SHA)}
        command=m.Worker._fixed_command(object(),reader);args=json.loads(command[-1])
        self.assertEqual(args[-1],'-PreparedBlockEightAfterCurrentSession');self.assertEqual(args[-2],str(m.r.c.ROOT/m.TARGET));self.assertEqual(command[1],'-B')
    def test_20_original_native_execution_function_except_exact_namespace_counts(self):
        source=inspect.getsource(old.execute).replace('631','684').replace("notify('prepared_six', value)","notify('prepared_eight', value)")
        source=source.replace('remaining_six_callbacks_returned_semantics_unqualified','block_eight_callbacks_returned_semantics_unqualified').replace("result['completed_callback_cases'] == 6","result['completed_callback_cases'] == 8").replace('len(cases.rows) == 6','len(cases.rows) == 8')
        self.assertEqual(inspect.getsource(m.execute),source)

if __name__=='__main__':
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(Contracts);result=unittest.TestResult();suite.run(result)
    print(json.dumps(dict(run=result.testsRun,errors=len(result.errors),failures=len(result.failures),skipped=len(result.skipped),failed_tests=[str(t)for t,_ in result.errors+result.failures],actual_native_started=False)))
    sys.exit(0 if result.wasSuccessful()else 2)
