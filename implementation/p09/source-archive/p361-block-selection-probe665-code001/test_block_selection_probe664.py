"""Observation-only binding and failure boundaries, never Native execution."""
import contextlib
import copy
import io
import json
from pathlib import Path
import sys
from types import SimpleNamespace as NS
import unittest
from unittest.mock import Mock,patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from test_block_bookmark_source660 import Guard,Reader
import block_selection_probe664 as m
import run_block_selection_probe664 as entry

def fixture():
    identity={'process_id':101};profile=dict(process_id=101,process_birth_100ns=123,cleanup_confirmed=True,owner_bound=True,assigned_before_initial_thread=True)
    trace=dict(schema_version='hwpx-agent.private.block-selection-probe664-trace/v1',case_index=1,phase='create_bookmarks',
        error_code=m.worker_code.EXPECTED_STOP,cleanup_error=None,input_leases_closed=True,probe_complete=True,
        artifacts={},block_ranges=[],block_content_support_qualified=False,P09_complete=False,
        sessions=[dict(label='save',quit_invoked=True,close_without_dirty_prompt_returned=True,remaining_owned_process_count=0,
            cleanup_error=None,process=identity)],dual_identity_evidence=[dict(channel_message_returned=True,
            observation=dict(compatibility_identity=identity,kernel_identity={'process_id':101},kernel_creation_filetime_100ns='123'))],
        selection_probe=[dict(label=label,read_returned=True,value={'modeled':True},error_kind=None,hresult=None)for label in m.LABELS])
    host=NS(schedule=NS(stopped=True,finish_attempted=True,done=False),scope=NS(closed=True,current=None,pending_admission=False,
        finished=[dict(case_index=1,case_status='failed')],sessions=[dict(startup_profile=profile)]),source_case=None)
    q=Reader();q.json=lambda path:trace
    return q,host,trace

def worker_result():
    return dict(schema_version=m.worker_code.RESULT,state='block_source_callbacks_failed_or_partial',error_code=m.worker_code.EXPECTED_STOP,
        diagnostic_only=True,probe_complete=True,source_capture_executed=False,completed_callback_cases=0,
        retained_live_or_uncertain_owners=0,planned_cases=1,planned_block_ranges=0,block_content_support_qualified=False,
        case_failure=dict(phase='create_bookmarks',error_code=m.worker_code.EXPECTED_STOP))

class Tests(unittest.TestCase):
    def test_parser_diagnostic_only_no_old_source_mode(self):
        self.assertTrue(entry.parser().parse_args(['--execute-probe-once']).execute_probe_once)
        for argv in(['--execute-source-once'],['--execute-probe-once','--inspect-only'],['--execute']):
            with contextlib.redirect_stderr(io.StringIO()),self.assertRaises(SystemExit):entry.parser().parse_args(argv)
    def test_one_kernel_producer_and_private_trace_not_capture(self):
        q,h,t=fixture();v=m.capture_metadata(q,h)
        self.assertTrue(v['diagnostic_producer_bound']);self.assertEqual(v['observations_recorded'],8)
        self.assertFalse(v['source_capture_executed']);self.assertFalse(v['selection_API_qualified'])
        self.assertEqual(q.final_fresh_hashes,len(q.snapshots))
    def test_false_or_failed_query_is_an_observation_never_API_success(self):
        q,h,t=fixture();t['selection_probe'][4].update(read_returned=False,value=None,error_kind='COMException',hresult='0x80004005')
        self.assertFalse(m.capture_metadata(q,h)['selection_API_qualified'])
    def test_partial_reordered_positive_or_raw_error_denied(self):
        for change in('partial','reorder','positive','artifact','raw_error','bool_case'):
            q,h,t=fixture()
            if change=='partial':t['selection_probe'].pop()
            elif change=='reorder':t['selection_probe'].reverse()
            elif change=='positive':t['block_content_support_qualified']=True
            elif change=='artifact':t['artifacts']['unexpected.hwpx']={}
            elif change=='bool_case':t['case_index']=True
            else:t['selection_probe'][0].update(read_returned=False,value=None,error_kind='PRIVATE',hresult='PRIVATE')
            with self.assertRaises(ValueError):m.capture_metadata(q,h)
    def test_live_owner_wrong_kernel_or_uncertain_cleanup_denied(self):
        for change in('live','kernel','cleanup','two_owners'):
            q,h,t=fixture()
            if change=='live':h.scope.current=object()
            elif change=='kernel':t['dual_identity_evidence'][0]['observation']['kernel_creation_filetime_100ns']='124'
            elif change=='two_owners':h.scope.sessions*=2
            else:t['sessions'][0]['remaining_owned_process_count']=1
            with self.assertRaises(ValueError):m.capture_metadata(q,h)
    def test_notice_preserves_intentional_failed_worker_and_no_authority(self):
        v=m.worker_code.source_result_notice(worker_result())
        self.assertTrue(v['diagnostic_observations_reported']);self.assertTrue(v['worker_failed_or_uncertain'])
        self.assertFalse(v['cleanup_confirmed']);self.assertFalse(v['source_capture_executed'])
    def test_wrong_notice_and_partial_never_observed(self):
        for key,value in [('probe_complete',False),('error_code','PRIVATE'),('completed_callback_cases',True)]:
            r=worker_result();r[key]=value;self.assertFalse(m.worker_code.source_result_notice(r)['diagnostic_observations_reported'])
        r=worker_result();r['schema_version']='old'
        with self.assertRaises(ValueError):m.worker_code.source_result_notice(r)
    def test_fixed_command_and_original_envelope(self):
        class Q:
            root=m.r.c.ROOT
            snapshots={}
            def pin(self,path):self.snapshots[path]={'sha256':m.worker_code.original.prior.original.BOOTSTRAP_SHA}
        q=Q();args=m.worker_code.Worker.__new__(m.worker_code.Worker)._fixed_command(q);inner=json.loads(args[-1])
        self.assertEqual(inner[-2],str(q.root/m.worker_code.TARGET));self.assertNotIn('-Command',inner)
        self.assertIs(m.worker_code.Worker.start_fixed_worker,m.worker_code.original.FixedWorker.start_fixed_worker)
        self.assertIn('implementation/p09/tools/block-selection-probe662-reflection.cs',q.snapshots)
    def code_proof(self):
        paths=m.SOURCES|m.prior.prepared.loaded_dependencies(m.r.c.ROOT)|{entry.SELF}
        return dict(state=entry.STATE,cleanup=True,fresh_inputs=1,final_fresh_hashes=1,all_new_tests_passed=True,
            Native_started=False,whole_source_execution_qualified=False,execution_dependency_paths=sorted(paths),
            source_pins=[dict(path=p,bytes=1,sha256='0'*64)for p in paths])
    def test_changed_code_and_bool_count_denied(self):
        for change in('sha','bool'):
            proof=self.code_proof()
            if change=='sha':proof['source_pins'][0]['sha256']='1'*64
            else:proof['fresh_inputs']=True
            q=Reader();q.json=lambda path:proof
            with patch.object(entry.publisher.codec,'unpack',side_effect=lambda v:v),self.assertRaises(ValueError):entry.load_code(q)
    def test_failed_qualification_never_starts_probe_worker(self):
        boundary=NS(source=Reader(),native_pin=Mock(),shell_pin=Mock())
        def fail(*args):args[-1].update(exit_code=2,cleanup=True);return {'state':'failed'}
        with patch.object(m,'absent'),patch.object(m.base.installed,'current_identity',return_value={}),patch.object(m.base,'Boundary',return_value=boundary),\
            patch.object(m.base.candidate,'SessionWorker'),patch.object(m.base.session,'SessionQualifier'),patch.object(m.prior.io,'run',side_effect=fail),\
            patch.object(m.worker_code,'Worker')as probe,self.assertRaises(ValueError):m.execute(Guard(),{},set(),{}, {},Mock(),{})
        probe.assert_not_called()
    def controller(self,change=None):
        class Boundary:
            def __init__(self,*args,**kw):
                self.source=Reader();self.native_pin=Mock();self.shell_pin=Mock();self.fingerprint='0'*64;self.closed=False
            def finish(self):self.closed=True
            def summary(self):return dict(closed=self.closed,readers={k:dict(fresh_inputs=1,final_fresh_hashes=1)for k in('source','native','shell','runtime')})
        hosts=[];guard=Guard();handoff=NS(consumed=True)
        def host(*args,**kw):
            h=NS(scope=NS(closed=True),worker_lease=NS(closed=True),begin=args[7],end=args[8]);hosts.append(h);return h
        def run(*args):
            record=args[-1];record.update(exit_code=0,cleanup=True)
            if args[5]=='hwpx-agent.private.crossref-session-worker-result/v1':return {'state':'modeled'}
            hosts[0].begin(1);hosts[0].end(1);record.update(exit_code=2,requests=13)
            result=worker_result()
            if change=='exit0':record['exit_code']=0
            elif change=='partial':result['probe_complete']=False
            elif change=='unexpected':result['error_code']='P09_XREF_BIND_OTHER_FAILURE'
            return result
        with patch.object(m,'absent'),patch.object(m.base.installed,'current_identity',return_value={'same':True}),\
            patch.object(m.base,'Boundary',Boundary),patch.object(m.base.candidate,'SessionWorker'),patch.object(m.base.session,'SessionQualifier'),\
            patch.object(m.base.batch,'issue_handoff',return_value=handoff),patch.object(m.prior.io,'run',side_effect=run),\
            patch.object(m.worker_code,'Worker',return_value=NS(closed=True,start_fixed_worker=Mock())),\
            patch.object(m.host_code,'Host',side_effect=host),patch.object(m.r.a,'AcceptanceReader',Reader),\
            patch.object(m,'capture_metadata',return_value={'source_capture_executed':False})as metadata:
            row={};value=m.execute(guard,{},set(),{}, {},Mock(),row)
        return value,row,guard
    def test_only_exact_diagnostic_exit2_with_closed_inputs_is_observed(self):
        value,row,g=self.controller();self.assertFalse(value['source_capture_executed'])
        self.assertTrue(row['batch_closed_for_final_audit']);self.assertTrue(row['capture_boundary']['closed'])
        self.assertEqual(g.events,['capture','batch_close'])
    def test_normal_capture_exit_or_unexpected_failure_not_promoted_to_diagnostic(self):
        for change in('exit0','partial','unexpected'):
            with self.assertRaises(ValueError):self.controller(change)
    def modeled_main(self,mode):
        guard=Guard();published=[];kept=[];shell_name=Path(m.base.candidate.original.SHELL).name
        proof=dict(worker_shell_pin=dict(path=shell_name,bytes=1,sha256='0'*64))
        with contextlib.ExitStack()as stack:
            for target,name,value in((m.prior.prepared,'require_absent',Mock()),(m,'absent',Mock()),
                (m.r.tools,'select_own_single_cpu',Mock(return_value={})),(m.r.shared.host,'configure_host_policy',Mock()),
                (m.sections,'guard_type',Mock(return_value=lambda:guard)),(m.r.a,'AcceptanceReader',Mock(side_effect=Reader)),
                (entry,'load_code',Mock(return_value=({},set(),proof))),
                (m.prior.prepared.runtime,'require_qualification',Mock(return_value={})),(m.prior.prepared.runtime,'verify_current_reader',Mock()),
                (m.base.installed.prerequisites,'inspect',Mock(return_value=dict(all_observed_prerequisites_passed=False)))):
                stack.enter_context(patch.object(target,name,value))
            execute=stack.enter_context(patch.object(m,'execute'))
            def retain(root,path,row):kept.append(copy.deepcopy(row));return row,{}
            stack.enter_context(patch.object(entry.publisher.retention,'retain',side_effect=retain))
            def publish(path,value):published.append(path);return dict(path=path,bytes=1,sha256='0'*64)
            stack.enter_context(patch.object(entry.publisher,'publish',side_effect=publish))
            with contextlib.redirect_stdout(io.StringIO()):code=entry.main([mode])
            execute.assert_not_called()
        return code,published,kept[-1]
    def test_inspect_never_claims_or_executes(self):
        code,published,row=self.modeled_main('--inspect-only');self.assertEqual(code,0)
        self.assertEqual(published,[entry.INSPECT]);self.assertFalse(row['native_claim_created'])
    def test_denied_prerequisite_never_claims_or_executes(self):
        code,published,row=self.modeled_main('--execute-probe-once');self.assertEqual(code,2)
        self.assertEqual(published,[entry.OUTPUT]);self.assertFalse(row['source_capture_executed'])

if __name__=='__main__':
    result=unittest.TestResult();unittest.defaultTestLoader.loadTestsFromTestCase(Tests).run(result)
    print(json.dumps(dict(run=result.testsRun,errors=len(result.errors),failures=len(result.failures),skipped=len(result.skipped),
        failed_tests=[t.id().rsplit('.',1)[-1]for t,_ in result.errors+result.failures],actual_native_started=False)))
    raise SystemExit(0 if result.wasSuccessful()else 2)

