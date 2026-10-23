"""New live handoff/fixed-eight/source/entry models; no actual Native/document IO."""
import contextlib,io,json,sys,unittest
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import Mock,patch
import crossref_qualified_batch as subject
import crossref_external_batch_runtime as runtime
import crossref_fixed_worker as fixed
import run_external_crossref_fixed_batch as entry
sys.path.insert(0,str(Path(__file__).resolve().parent))
import test_crossref_preassigned_session_scope as prior_scope
import test_crossref_session_qualification as prior_kernel

ROOT={'process_id':501,'creation_filetime_100ns':'133000000000000001','kernel_handle_observation':True}
FINGERPRINT='a'*64


class BatchModel:
    def __init__(self):
        self.created=[];self.events=[];self.begun=[];self.ended=[];self.fail_begin=False;self.fail_end=False
        windows=subject.sessions.startup.limits.c.Windows.__new__(subject.sessions.startup.limits.c.Windows)
        windows.k=NS(WaitForSingleObject=lambda h,m:258 if self.created[-1].alive else 0)
        windows.accounting=lambda job:dict(active_processes=0)
        self.guard=NS(check=Mock(),windows=windows);self.worker=NS();self.lease=NS(observe=Mock(),close=Mock(),closed=False)
        self.patchers=[patch.object(subject.original.sessions.startup,'PreassignedNativeStartup',side_effect=self.factory),
            patch.object(subject.sessions,'WorkerKernelLease',return_value=self.lease),
            patch.object(subject.sessions.startup,'parent_without_prompt_kill',return_value={'job_present':False})]
    def factory(self,*args):
        item=prior_scope.FakeStartup(len(self.created)+1,self.events);item.process=987;item.owner_job=NS(job=543)
        self.created.append(item);return item
    def begin(self,index):
        self.begun.append(index)
        if self.fail_begin:raise ValueError('MODEL_SOURCE_BEGIN_FAILED')
    def end(self,index):
        self.ended.append(index)
        if self.fail_end:raise ValueError('MODEL_SOURCE_END_FAILED')
    def __enter__(self):
        self.mocks=[p.start()for p in self.patchers]
        self.handoff=subject.LiveHandoff(subject._ISSUER,self.guard,ROOT,FINGERPRINT)
        self.host=subject.FixedEightHost(self.guard,self.worker,self.handoff,ROOT,FINGERPRINT,lambda:None,lambda:None,self.begin,self.end)
        return self
    def __exit__(self,*args):
        for p in reversed(self.patchers):p.stop()
    def release(self):
        return json.loads(self.host.release_worker(json.dumps(dict(schema_version=subject.READY,worker_identity=prior_kernel.worker_identity()),separators=(',',':'))))
    def send(self,op='checkpoint',**extra):
        raw=json.dumps(dict(schema_version=subject.original.REQUEST,sequence=self.host.protocol.protocol.sequence+1,
            case_index=self.host.scope.case_index,operation=op,**extra),separators=(',',':'))
        out=json.loads(self.host.respond(raw))
        if out['acknowledged']and extra.get('step')in('save_session_close','reopen_session_close'):self.host.scope.current.alive=False
        return out
    def admit(self,d):
        identity={key:d[key]for key in('process_id','session_id','created_at_utc','executable_sha256')};identity['window_handle_binds_exact_process']=True
        return self.send('admit_owner',identity=identity,window_handle=123)
    def case(self,expect_end=True):
        for step in subject.original.original.STEPS:
            out=self.send(step=step)
            if step=='final_source_check'and not expect_end:return out
            assert out['acknowledged']
            if step in('create_save_session','create_reopen_session'):assert self.admit(out['owner_descriptor'])['acknowledged']
        return self.send('finish',case_status='returned')


def completed_qualification():
    qualifier=subject.sessions.SessionQualifier.__new__(subject.sessions.SessionQualifier)
    guard=NS(windows=NS());qualifier.guard=guard;qualifier.finished=True;qualifier.stopped=False;qualifier.lifecycle_candidate=True
    qualifier.current=NS(closed=True,profile={'cleanup_confirmed':True});qualifier.worker=NS(closed=True);qualifier.worker_lease=NS(closed=True)
    result=dict(state='session_worker_lifecycle_returned_source_and_native_qualification_pending',COM_owner_observed=True,
        cleanup=prior_kernel.cleanup(),document_opened_or_saved=False,fixed_eight_executed=False)
    return guard,qualifier,result


def modeled_entry(preflight,passed):
    class Guard:
        def __init__(self):self.windows=NS();self.samples=[];self.cleanup=False
        def acquire(self):pass
        def check(self,force=False):pass
        def close(self):self.cleanup=True
    shell=dict(path='powershell.exe',bytes=1000,sha256='a'*64)
    def reader(root,check):
        item=NS(snapshots={entry.CODE:dict(path=entry.CODE,bytes=1,sha256='b'*64)},final_fresh_hashes=0)
        def finish():item.final_fresh_hashes=len(item.snapshots)
        item.pin=Mock(return_value=shell);item.fresh_pin=Mock(return_value=shell);item.finish=finish;return item
    patches=[patch.object(entry.r.tools,'select_own_single_cpu',return_value={}),
        patch.object(entry.r.shared.host,'configure_host_policy'),patch.object(entry.r.shared.final,'guard_type',return_value=Guard),
        patch.object(entry.r.shared.baseline,'guard_type',return_value=Guard),patch.object(entry.r.a,'AcceptanceReader',side_effect=reader),
        patch.object(entry,'load_manifest',return_value=({'external_shell_pins':[shell]}, {}, set())),
        patch.object(entry.installed,'runtime_pin_matches'),patch.object(entry.installed,'current_identity',return_value=ROOT),
        patch.object(entry.prerequisites,'inspect',return_value={'all_observed_prerequisites_passed':passed}),
        patch.object(entry.runtime,'absent_attempts'),patch.object(entry.runtime,'execute'),patch.object(entry,'publish',return_value={'path':'MODEL_ONLY'})]
    mocks=[]
    try:
        mocks=[p.start()for p in patches]
        argv=['--preflight-only','--inspection-run','8']if preflight else['--execute-qualified-fixed-eight']
        with contextlib.redirect_stdout(io.StringIO()):status=entry.main(argv)
        return status,mocks[-2].call_count,mocks[-1].call_args_list
    finally:
        for p in reversed(patches):p.stop()


class EntryContracts(unittest.TestCase):
    def test_01_fixed_eight_real_order_with_case_boundaries_and_sixteen_models(self):
        with BatchModel()as m:
            self.assertTrue(m.release()['acknowledged'])
            for _ in range(8):self.assertTrue(m.case()['acknowledged'])
            self.assertEqual(m.host.protocol.protocol.sequence,152);self.assertEqual(m.begun,list(range(1,9)));self.assertEqual(m.ended,m.begun)
            self.assertEqual(len(m.host.scope.sessions),16);self.assertTrue(m.handoff.consumed);self.assertIsNone(m.host.source_case)
            self.assertFalse(m.host.summary()['native_execution_authorized'])
            self.assertTrue(all(call.kwargs=={'refresh_image':False}for call in m.lease.observe.call_args_list))
    def test_02_source_begin_failure_stops_before_native_creation(self):
        with BatchModel()as m:
            m.release();m.fail_begin=True;self.assertFalse(m.send(step='prepare_slot')['acknowledged']);self.assertEqual(m.created,[])
            self.assertTrue(m.host.scope.stopped)
    def test_03_final_source_failure_never_becomes_returned_case(self):
        with BatchModel()as m:
            m.release();m.fail_end=True;self.assertFalse(m.case(False)['acknowledged']);self.assertEqual(len(m.host.scope.sessions),2)
            self.assertTrue(m.send('finish',case_status='failed')['acknowledged']);self.assertEqual(m.host.source_case,1)
    def test_04_case_input_cannot_run_before_current_worker_release(self):
        with BatchModel()as m:
            with self.assertRaises(ValueError):m.send(step='prepare_slot')
            self.assertEqual(m.begun,[]);self.assertEqual(m.created,[])
    def test_05_worker_release_is_once_and_closed_schema(self):
        with BatchModel()as m:
            m.release()
            with self.assertRaises(ValueError):m.release()
        with BatchModel()as m:
            with self.assertRaises(ValueError):m.host.release_worker('{"approved":true}')
    def test_06_handoff_rejects_wrong_issuer(self):
        with self.assertRaises(ValueError):subject.LiveHandoff(object(),None,ROOT,FINGERPRINT)
    def test_07_handoff_one_use_only(self):
        guard=object();handoff=subject.LiveHandoff(subject._ISSUER,guard,ROOT,FINGERPRINT);handoff.consume(guard,ROOT,FINGERPRINT)
        with self.assertRaises(ValueError):handoff.consume(guard,ROOT,FINGERPRINT)
    def test_08_same_pid_other_kernel_lifetime_cannot_consume(self):
        guard=object();handoff=subject.LiveHandoff(subject._ISSUER,guard,ROOT,FINGERPRINT)
        with self.assertRaises(ValueError):handoff.consume(guard,dict(ROOT,creation_filetime_100ns='other'),FINGERPRINT)
        self.assertFalse(handoff.consumed)
    def test_09_other_guard_or_source_fingerprint_cannot_consume(self):
        guard=object();handoff=subject.LiveHandoff(subject._ISSUER,guard,ROOT,FINGERPRINT)
        for other,digest in((object(),FINGERPRINT),(guard,'b'*64)):
            with self.assertRaises(ValueError):handoff.consume(other,ROOT,digest)
    def test_10_saved_receipt_or_boolean_is_not_live_handoff(self):
        with BatchModel()as m:
            for data in(True,{'qualified':True},'saved-receipt'):
                with self.assertRaises(ValueError):subject.FixedEightHost(m.guard,m.worker,data,ROOT,FINGERPRINT,lambda:None,lambda:None,m.begin,m.end)
    def test_11_completed_current_session_and_sources_issue_handoff_only(self):
        guard,qualifier,result=completed_qualification()
        with patch.object(subject.sessions.startup,'parent_without_prompt_kill',return_value={'job_present':False}):
            value=subject.issue_handoff(guard,qualifier,result,True,ROOT,dict(ROOT),FINGERPRINT)
        self.assertIs(type(value),subject.LiveHandoff);self.assertFalse(value.consumed)
    def test_12_unclosed_source_or_changed_creator_cannot_issue(self):
        guard,qualifier,result=completed_qualification()
        for source,after in((False,ROOT),(True,dict(ROOT,process_id=999))):
            with self.assertRaises(ValueError):subject.issue_handoff(guard,qualifier,result,source,ROOT,after,FINGERPRINT)
    def test_13_incomplete_or_stopped_candidate_cannot_issue(self):
        for key,value in(('finished',False),('stopped',True),('lifecycle_candidate',False)):
            guard,qualifier,result=completed_qualification();setattr(qualifier,key,value)
            with self.assertRaises(ValueError):subject.issue_handoff(guard,qualifier,result,True,ROOT,ROOT,FINGERPRINT)
    def test_14_boolean_zero_cleanup_does_not_issue(self):
        guard,qualifier,result=completed_qualification();result['cleanup']['remaining_owned_process_count']=False
        with self.assertRaises(ValueError):subject.issue_handoff(guard,qualifier,result,True,ROOT,ROOT,FINGERPRINT)
    def test_15_missing_worker_query_close_cannot_issue(self):
        guard,qualifier,result=completed_qualification();qualifier.worker_lease.closed=False
        with self.assertRaises(ValueError):subject.issue_handoff(guard,qualifier,result,True,ROOT,ROOT,FINGERPRINT)
    def test_16_original_parent_jobless_condition_still_applies_to_handoff(self):
        guard,qualifier,result=completed_qualification()
        with patch.object(subject.sessions.startup,'parent_without_prompt_kill',side_effect=ValueError('UNSAFE_PARENT')):
            with self.assertRaises(ValueError):subject.issue_handoff(guard,qualifier,result,True,ROOT,ROOT,FINGERPRINT)
    def test_17_new_fixed_worker_role_requires_explicit_program_expectation(self):
        worker,pin=prior_kernel.kernel_model();worker.profile['role']='private_fixed_eight_worker'
        with self.assertRaises(ValueError):subject.sessions.WorkerKernelLease(worker,prior_kernel.worker_identity(),pin)
        value=subject.sessions.WorkerKernelLease(worker,prior_kernel.worker_identity(),pin,expected_role='private_fixed_eight_worker')
        worker.process.poll=lambda:0;value.close()
    def test_18_unknown_expected_role_rejects_before_open(self):
        worker,pin=prior_kernel.kernel_model()
        with self.assertRaises(ValueError):subject.sessions.WorkerKernelLease(worker,prior_kernel.worker_identity(),pin,expected_role='ANY_PROCESS')
        worker.windows.k.OpenProcess.assert_not_called()
    def test_19_frame_kernel_checks_do_not_repeat_complete_image_hash(self):
        worker,pin=prior_kernel.kernel_model();fresh=Mock(side_effect=pin)
        value=subject.sessions.WorkerKernelLease(worker,prior_kernel.worker_identity(),fresh)
        for _ in range(4):value.observe(refresh_image=False)
        self.assertEqual(fresh.call_count,1);self.assertEqual(worker.observe.call_count,5)
        worker.process.poll=lambda:0;value.close()
    def test_20_skipping_frame_hash_never_skips_kernel_birth_check(self):
        worker,pin=prior_kernel.kernel_model();value=subject.sessions.WorkerKernelLease(worker,prior_kernel.worker_identity(),pin)
        value.identity['created_at_utc']=subject.sessions.startup.utc_identity(prior_kernel.BIRTH+1)
        with self.assertRaises(ValueError):value.observe(refresh_image=False)
        worker.process.poll=lambda:0;value.close()
    def test_21_nonboolean_refresh_selector_rejected(self):
        worker,pin=prior_kernel.kernel_model();value=subject.sessions.WorkerKernelLease(worker,prior_kernel.worker_identity(),pin)
        with self.assertRaises(ValueError):value.observe(refresh_image=0)
        worker.process.poll=lambda:0;value.close()
    def test_22_default_image_refresh_still_rejects_current_image_drift(self):
        worker,pin=prior_kernel.kernel_model();fresh=Mock(side_effect=pin);value=subject.sessions.WorkerKernelLease(worker,prior_kernel.worker_identity(),fresh)
        fresh.side_effect=lambda:dict(path='powershell.exe',bytes=1000,sha256='b'*64)
        with self.assertRaises(ValueError):value.observe()
        worker.process.poll=lambda:0;value.close()
    def test_23_fixed_worker_command_has_no_subset_or_generic_path(self):
        paths=[];reader=NS(root=runtime.r.c.ROOT,snapshots={fixed.prior.original.BOOTSTRAP:{'sha256':fixed.prior.original.BOOTSTRAP_SHA}},pin=paths.append)
        args=json.loads(fixed.command(reader)[-1]);self.assertEqual(args[-1],'-FixedEightAfterSession');self.assertEqual(paths,list(fixed.SOURCES))
        self.assertNotIn('-ExecuteNative',args)
    def test_24_native_entry_has_no_retry_selector(self):
        args=entry.parser().parse_args(['--execute-qualified-fixed-eight']);self.assertEqual(entry.output_name(args),entry.OUTPUT)
        args=entry.parser().parse_args(['--execute-qualified-fixed-eight','--inspection-run','2'])
        with self.assertRaises(ValueError):entry.output_name(args)
    def test_25_preflight_namespace_separate_and_requires_explicit_run(self):
        args=entry.parser().parse_args(['--preflight-only','--inspection-run','1']);self.assertNotEqual(entry.output_name(args),entry.OUTPUT)
        with self.assertRaises(ValueError):entry.output_name(entry.parser().parse_args(['--preflight-only']))
    def test_26_execution_and_preflight_cannot_be_combined(self):
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):entry.parser().parse_args(['--preflight-only','--execute-qualified-fixed-eight'])
    def test_27_only_fixed_eight_artifact_directories_exist_in_selector(self):
        self.assertEqual(len({runtime.artifact_directory(i)for i in range(1,9)}),8)
        for index in(True,0,9):
            with self.assertRaises(ValueError):runtime.artifact_directory(index)
    def test_28_ready_payload_size_bound_before_kernel_open(self):
        with BatchModel()as m:
            with self.assertRaises(ValueError):m.host.release_worker('x'*4097)
            m.mocks[1].assert_not_called()
    def test_29_partial_live_native_drain_never_forces_close(self):
        current=NS(closed=False,process=987,owner_job=NS(job=123))
        windows=NS(k=NS(WaitForSingleObject=Mock(return_value=258)),accounting=Mock())
        subject.wait_exited_tree(current,windows);windows.accounting.assert_not_called();self.assertFalse(current.closed)
    def test_30_exited_native_tree_counter_is_observed_to_zero(self):
        current=NS(closed=False,process=987,owner_job=NS(job=123))
        windows=NS(k=NS(WaitForSingleObject=Mock(return_value=0)),accounting=Mock(side_effect=[{'active_processes':1},{'active_processes':0}]))
        with patch.object(subject.time,'sleep')as sleep:subject.wait_exited_tree(current,windows)
        sleep.assert_called_once_with(.05);self.assertEqual(windows.accounting.call_count,2)
    def test_31_boundary_uses_fresh_pin_for_repeated_native_image_checks(self):
        manifest={'tools/p09/example.py':dict(path='tools/p09/example.py',bytes=1,sha256='c'*64)};created=[]
        shell=dict(path='powershell.exe',bytes=1000,sha256='b'*64)
        def reader(root,check):
            instance=NS(root=root,snapshots={},final_fresh_hashes=0)
            def pin(name):
                if root==runtime.r.c.ROOT:value=manifest[name]
                elif root==Path(runtime.installed.native.EXECUTABLE).parent:value=dict(path=name,bytes=runtime.installed.native.EXECUTABLE_BYTES,sha256=runtime.installed.native.EXECUTABLE_SHA)
                elif root==runtime.installed.fixed.PYTHON.parent:value=dict(path=name,bytes=107312,sha256=runtime.installed.RUNTIME_SHA)
                else:value=shell
                instance.snapshots[name]=value;return value
            def finish():instance.final_fresh_hashes=len(instance.snapshots)
            instance.pin=Mock(side_effect=pin);instance.fresh_pin=Mock(side_effect=pin);instance.finish=Mock(side_effect=finish)
            created.append(instance);return instance
        guard=NS(check=Mock())
        with patch.object(runtime.r.a,'AcceptanceReader',side_effect=reader):
            boundary=runtime.Boundary(guard,manifest,set(manifest),'case1',shell)
            boundary.native_pin();boundary.native_pin();boundary.shell_pin();boundary.finish()
        self.assertEqual(boundary.native.fresh_pin.call_count,2);self.assertEqual(boundary.shell.fresh_pin.call_count,1)
        self.assertTrue(boundary.closed);self.assertTrue(all(x.finish.call_count==1 for x in created))
        with self.assertRaises(ValueError):boundary.finish()
    def test_32_case_boundaries_are_fresh_one_at_a_time_not_history_replay(self):
        cases=runtime.CaseInputs(None,{},None)
        with self.assertRaises(ValueError):cases.native_pin()
        def boundary(guard,manifest,paths,label,shell):
            self.assertEqual(paths,runtime.CASE_PATHS)
            return NS(label=label,finish=Mock(),summary=lambda:dict(label=label,closed=True))
        with patch.object(runtime,'Boundary',side_effect=boundary):
            cases.begin(1)
            with self.assertRaises(ValueError):cases.begin(2)
            cases.end(1);cases.begin(2);cases.end(2)
        self.assertEqual([r['label']for r in cases.rows],['case1','case2']);self.assertIsNone(cases.current)
    def test_33_source_stop_reason_is_preserved_without_raw_values(self):
        with BatchModel()as m:
            m.release();m.fail_begin=True;m.send(step='prepare_slot')
            self.assertEqual(m.host.summary()['source_primary_error'],'MODEL_SOURCE_BEGIN_FAILED')
    def test_34_artifact_binding_requires_all_sixteen_closed_native_sessions(self):
        host=NS(protocol=NS(protocol=NS(case_index=1,stopped=False)),scope=NS(sessions=[]))
        with self.assertRaises(ValueError):runtime.capture_artifacts(None,host)
    def test_35_public_preflight_cannot_execute_even_if_prerequisites_pass(self):
        status,executions,writes=modeled_entry(True,True)
        self.assertEqual(status,0);self.assertEqual(executions,0);self.assertEqual(len(writes),1)
        self.assertNotEqual(writes[0].args[0],entry.CLAIM);self.assertFalse(writes[0].args[1]['native_claim_created'])
    def test_36_failed_current_prerequisites_prevent_native_claim_and_execution(self):
        status,executions,writes=modeled_entry(False,False)
        self.assertEqual(status,2);self.assertEqual(executions,0);self.assertEqual(len(writes),1)
        self.assertNotEqual(writes[0].args[0],entry.CLAIM);self.assertFalse(writes[0].args[1]['native_claim_created'])
