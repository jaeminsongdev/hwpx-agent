"""Pure005 entry/runtime composition models. No process, claim, actual output or Native starts."""
import contextlib,copy,io,json,unittest
from types import SimpleNamespace as NS
from unittest.mock import Mock,patch
import run_external_crossref_fixed_batch005 as entry
import crossref_external005_runtime as runtime

def manifest_model():
    paths=sorted(runtime.CASE_PATHS|{entry.SELF})
    pins={name:dict(path=name,bytes=10,sha256='a'*64)for name in paths}
    for name,(size,sha)in runtime.fixed_input_pins().items():pins[name]=dict(path=name,bytes=size,sha256=sha)
    proof=dict(state=entry.CODE_STATE,generation=5,cleanup=True,fresh_inputs=3,final_fresh_hashes=3,
        contracts=dict(run=32,errors=0,failures=0,skipped=0),entry_dependency_paths=paths,source_pins=list(pins.values()))
    ready=dict(state=entry.READY_STATE,generation=5,cleanup=True,code_proof_sha256='b'*64,native_startup_qualified=False,source_pins=copy.deepcopy(list(pins.values())))
    records={entry.NAMES['code']:proof,entry.NAMES['ready']:ready}
    reader=NS(snapshots={entry.NAMES['code']:dict(path=entry.NAMES['code'],bytes=1,sha256='b'*64)},
        json=Mock(side_effect=lambda name:entry.layout.pack(records[name])),pin=Mock(side_effect=lambda name:pins[name]))
    return reader,records,pins

@contextlib.contextmanager
def modeled_main(preflight,passed=True,ready_failure=False,execute_effect=None):
    class Guard:
        def __init__(self):self.windows=NS();self.samples=[];self.cleanup=False
        def acquire(self):pass
        def check(self,force=False):pass
        def close(self):self.cleanup=True
    shell=dict(path='powershell.exe',bytes=100,sha256='a'*64)
    def reader(root,check):
        value=NS(snapshots={entry.NAMES['code']:dict(path=entry.NAMES['code'],bytes=1,sha256='b'*64)},final_fresh_hashes=0,
            pin=Mock(return_value=shell),fresh_pin=Mock(return_value=shell))
        def finish():value.final_fresh_hashes=len(value.snapshots)
        value.finish=finish;return value
    patches=[patch.object(entry.r.tools,'select_own_single_cpu',return_value={}),patch.object(entry.r.shared.host,'configure_host_policy'),
        patch.object(entry.r.shared.final,'guard_type',return_value=Guard),patch.object(entry.r.shared.baseline,'guard_type',return_value=Guard),
        patch.object(entry.r.a,'AcceptanceReader',side_effect=reader),patch.object(entry,'load_manifest',
            side_effect=ValueError('MODEL_READY_MISSING')if ready_failure else None,return_value=({'external_shell_pins':[shell]},{},set())),
        patch.object(entry.host_profile,'require_qualification',return_value={'MODEL_ONLY':True}),
        patch.object(entry.host_profile,'verify_current_reader',return_value={'MODEL_ONLY':True}),
        patch.object(entry.installed,'current_identity',return_value={'MODEL_CREATOR':True}),
        patch.object(entry.prerequisites,'inspect',return_value={'all_observed_prerequisites_passed':passed}),
        patch.object(runtime,'absent_attempts'),patch.object(runtime,'execute',side_effect=execute_effect,return_value={'cases':[{}]*8}),
        patch.object(entry,'publish_small',side_effect=lambda path,row:dict(path=path,bytes=1,sha256='a'*64)),
        patch.object(entry.publication,'publish_final',return_value={'path':'MODEL_FINAL_ONLY'}),
        patch.object(entry.Path,'exists',return_value=False),patch.object(entry.Path,'is_symlink',return_value=False),
        patch.object(entry.Path,'is_junction',return_value=False),patch.object(entry.Path,'is_dir',return_value=True),patch.object(entry.Path,'mkdir')]
    with contextlib.ExitStack()as stack:
        mocks=[stack.enter_context(p)for p in patches];output=io.StringIO()
        with contextlib.redirect_stdout(output):code=entry.main(['--preflight-generation-005']if preflight else['--execute-generation-005-fixed-eight'])
        final=entry.publication.publish_final.call_args.args[1]if not preflight else entry.publish_small.call_args.args[1]
        yield NS(code=code,row=final,mocks=mocks,publish=entry.publish_small,final=entry.publication.publish_final,
            execute=runtime.execute,load=entry.load_manifest,stdout=output.getvalue())

@contextlib.contextmanager
def modeled_runtime(qualification_failed=False,batch_failed=False,count=8):
    boundaries=[];record={};guard=NS(windows=NS())
    def boundary(*args):
        obj=NS(source=NS(),closed=False,fingerprint='MODEL005',native_pin=Mock(),shell_pin=Mock(),label=args[3])
        def finish():obj.closed=True
        obj.finish=finish;obj.summary=lambda:dict(label=obj.label,closed=obj.closed);boundaries.append(obj);return obj
    cases=NS(rows=[{}]*8,current=None,native_pin=Mock(),begin=Mock(),end=Mock())
    worker=NS(start_session_worker=Mock());full=NS(start_fixed_worker=Mock());handoff=NS(consumed=True)
    def transport(guard,process,source,start,handler,schema,env,notify,attempt):
        notify(dict(state='MODEL_TRANSPORT_NOTICE'))
        if 'session-worker'in schema:
            attempt.update(exit_code=2 if qualification_failed else 0,cleanup=True);return {'MODEL_QUALIFICATION':True}
        if batch_failed:
            cases.rows=[];cases.current=NS(summary=lambda:dict(label='case1',closed=False));attempt.update(exit_code=2,cleanup=True)
            raise ValueError('MODEL_FIXED_CASE_FAILURE')
        attempt.update(exit_code=0,cleanup=True)
        return dict(state='fixed_eight_callbacks_returned_semantics_unqualified',completed_callback_cases=count,host_messages=152,
            retained_live_or_uncertain_owners=0,probe_lease_closed=True)
    with contextlib.ExitStack()as stack:
        for p in(patch.object(runtime,'Boundary',side_effect=boundary),patch.object(runtime,'CaseInputs',return_value=cases),
            patch.object(runtime,'absent_attempts'),patch.object(runtime.installed,'current_identity',return_value={'MODEL_CREATOR':True}),
            patch.object(runtime.original.candidate,'SessionWorker',return_value=worker),patch.object(runtime.original.session,'SessionQualifier',return_value=NS()),
            patch.object(runtime.original.batch,'issue_handoff',return_value=handoff),patch.object(runtime.capture,'Fixed005Worker',return_value=full),
            patch.object(runtime.original.batch,'FixedEightHost',return_value=NS()),patch.object(runtime.original.io,'run',side_effect=transport),
            patch.object(runtime.original.session.startup,'parent_without_prompt_kill'),patch.object(runtime,'capture_artifacts',return_value={'cases':[{}]*8})):
            stack.enter_context(p)
        yield NS(guard=guard,record=record,boundaries=boundaries,cases=cases,handoff=handoff,notify=Mock(),
            execute=lambda:runtime.execute(guard,{},runtime.CASE_PATHS,{}, {},lambda *args:None,record),
            fixed=runtime.capture.Fixed005Worker,capture=runtime.capture_artifacts)

class Entry005(unittest.TestCase):
    def test_01_fixed005_paths_never_point_at_consumed_generation(self):
        self.assertEqual(entry.NAMES['output'],entry.publication.OUTPUT)
        for key in('claim','output','preflight','scratch'):self.assertIn('005',entry.NAMES[key])
        self.assertNotIn('run_external_crossref_fixed_batch.py',entry.SELF)
    def test_02_parser_accepts_only_fixed005_modes(self):
        args=entry.parser().parse_args(['--preflight-generation-005']);self.assertTrue(args.preflight_generation_005)
        self.assertTrue(entry.parser().parse_args(['--execute-generation-005-fixed-eight']).execute_generation_005_fixed_eight)
    def test_03_old_generations_subsets_paths_retry_and_conflicting_modes_are_denied(self):
        for args in([],['--execute-generation-004-fixed-eight'],['--generation','5'],['--case','1'],['--retry'],
            ['--preflight-generation-005','--execute-generation-005-fixed-eight']):
            with contextlib.redirect_stderr(io.StringIO()),self.assertRaises(SystemExit):entry.parser().parse_args(args)
    def test_04_current_code_manifest_and_fixed_inputs_are_checked(self):
        reader,_,_=manifest_model()
        with patch.object(entry,'loaded_paths',return_value={entry.SELF}):
            proof,pins,paths=entry.load_manifest(reader)
        self.assertEqual(proof['generation'],5);self.assertTrue(runtime.CASE_PATHS<=paths);self.assertTrue(set(runtime.fixed_input_pins())<=paths)
    def test_05_readiness_is_checked_only_when_required_and_current(self):
        reader,_,_=manifest_model()
        with patch.object(entry,'loaded_paths',return_value={entry.SELF}):entry.load_manifest(reader,True)
        self.assertIn(entry.NAMES['ready'],[c.args[0]for c in reader.json.call_args_list])
    def test_06_failed_wrong_generation_or_unclosed_code_never_admits(self):
        for key,value in(('state','FAILED'),('generation',4),('cleanup',False),('final_fresh_hashes',0)):
            reader,records,_=manifest_model();records[entry.NAMES['code']][key]=value
            with patch.object(entry,'loaded_paths',return_value=set()),self.assertRaises(ValueError):entry.load_manifest(reader)
    def test_07_failed_incomplete_or_skipped_contracts_never_admit(self):
        for key,value in(('run',23),('errors',1),('failures',1),('skipped',1)):
            reader,records,_=manifest_model();records[entry.NAMES['code']]['contracts'][key]=value
            with patch.object(entry,'loaded_paths',return_value=set()),self.assertRaises(ValueError):entry.load_manifest(reader)
    def test_08_missing_loaded_module_or_case_source_is_denied(self):
        reader,records,_=manifest_model()
        with patch.object(entry,'loaded_paths',return_value={'tools/p09/MISSING_IMPORT.py'}),self.assertRaises(ValueError):entry.load_manifest(reader)
        reader,records,_=manifest_model();records[entry.NAMES['code']]['entry_dependency_paths'].remove(runtime.SELF)
        with patch.object(entry,'loaded_paths',return_value=set()),self.assertRaises(ValueError):entry.load_manifest(reader)
    def test_09_duplicate_paths_or_missing_entry_is_denied(self):
        for duplicate in(True,False):
            reader,records,_=manifest_model();paths=records[entry.NAMES['code']]['entry_dependency_paths']
            if duplicate:paths.append(paths[0])
            else:paths.remove(entry.SELF)
            with patch.object(entry,'loaded_paths',return_value=set()),self.assertRaises(ValueError):entry.load_manifest(reader)
    def test_10_changed_live_source_pin_is_denied(self):
        reader,_,pins=manifest_model();reader.pin=Mock(side_effect=lambda name:{**pins[name],'sha256':'0'*64})
        with patch.object(entry,'loaded_paths',return_value=set()),self.assertRaises(ValueError):entry.load_manifest(reader)
    def test_11_readiness_failure_is_not_native_authority(self):
        for key,value in(('state','FAILED'),('generation',4),('cleanup',False),('native_startup_qualified',True)):
            reader,records,_=manifest_model();records[entry.NAMES['ready']][key]=value
            with patch.object(entry,'loaded_paths',return_value=set()),self.assertRaises(ValueError):entry.load_manifest(reader,True)
    def test_12_readiness_cannot_bind_a_different_code_proof(self):
        reader,records,_=manifest_model();records[entry.NAMES['ready']]['code_proof_sha256']='0'*64
        with patch.object(entry,'loaded_paths',return_value=set()),self.assertRaises(ValueError):entry.load_manifest(reader,True)
    def test_13_missing_or_stale_readiness_source_cannot_be_reused(self):
        for missing in(True,False):
            reader,records,_=manifest_model();pins=records[entry.NAMES['ready']]['source_pins']
            if missing:pins[:]=[p for p in pins if p['path']!=entry.SELF]
            else:
                for p in pins:
                    if p['path']==entry.SELF:p['sha256']='0'*64
            with patch.object(entry,'loaded_paths',return_value=set()),self.assertRaises(ValueError):entry.load_manifest(reader,True)
    def test_14_wrong_fixed_probe_input_is_denied_after_code_check(self):
        reader,records,pins=manifest_model();pins[runtime.capture.namespace.PROBE]['sha256']='0'*64
        records[entry.NAMES['code']]['source_pins']=copy.deepcopy(list(pins.values()))
        with patch.object(entry,'loaded_paths',return_value=set()),self.assertRaises(ValueError):entry.load_manifest(reader)
    def test_15_runtime_ready_selector_is_strict_boolean(self):
        reader,_,_=manifest_model()
        with self.assertRaises(ValueError):entry.load_manifest(reader,1)
    def test_16_boundary_reuses_original_host_image_guard_and_adds_exact005_probe(self):
        def init(obj,*args,**kwargs):obj.source=NS(snapshots={runtime.capture.namespace.PROBE:dict(bytes=runtime.capture.PROBE_PIN[0],sha256=runtime.capture.PROBE_PIN[1])})
        with patch.object(runtime.original.Boundary,'__init__',autospec=True,side_effect=init)as old:
            runtime.Boundary(NS(),{},set(),'MODEL005',{})
        self.assertTrue(old.call_args.kwargs['current004'])
    def test_17_wrong005_probe_cannot_pass_even_with_a_manifest(self):
        def init(obj,*args,**kwargs):obj.source=NS(snapshots={runtime.capture.namespace.PROBE:dict(bytes=1,sha256='0'*64)})
        with patch.object(runtime.original.Boundary,'__init__',autospec=True,side_effect=init),self.assertRaises(ValueError):runtime.Boundary(NS(),{},set(),'MODEL005',{})
    def test_18_case_inputs_reject_bool_subset_and_wrong_order_before_reader(self):
        cases=runtime.CaseInputs(NS(),{},{});
        for index in(True,0,9,2):
            with patch.object(runtime,'Boundary')as reader,self.assertRaises(ValueError):cases.begin(index)
            reader.assert_not_called()
    def test_19_case_end_and_native_pin_require_same_active_source_boundary(self):
        cases=runtime.CaseInputs(NS(),{},{});
        for action in(lambda:cases.end(1),cases.native_pin,cases.shell_pin):
            with self.assertRaises(ValueError):action()
    def test_20_incomplete_execution_closure_fails_before_any_worker(self):
        with patch.object(runtime.original.candidate,'SessionWorker')as worker,self.assertRaises(ValueError):runtime.execute(NS(),{},set(),{},{},Mock(),{})
        worker.assert_not_called()
    def test_21_failed_qualification_never_creates_fixed_worker(self):
        with modeled_runtime(qualification_failed=True)as m:
            with self.assertRaises(ValueError):m.execute()
            m.fixed.assert_not_called();m.capture.assert_not_called()
    def test_22_full_composition_uses005_worker_closed_handoff_and_original_capture_gate(self):
        with modeled_runtime()as m:
            self.assertEqual(len(m.execute()['cases']),8);m.fixed.assert_called_once();m.capture.assert_called_once()
            self.assertTrue(m.record['same_invocation_handoff_consumed']);self.assertEqual(len(m.record['case_source_boundaries']),8)
    def test_23_partial_case_source_and_handoff_are_preserved_on_failure(self):
        with modeled_runtime(batch_failed=True)as m:
            with self.assertRaises(ValueError):m.execute()
            self.assertEqual(m.record['partial_case_source_boundary'],dict(label='case1',closed=False));self.assertTrue(m.record['same_invocation_handoff_consumed'])
    def test_24_seven_callbacks_cannot_be_promoted_to_whole_eight(self):
        with modeled_runtime(count=7)as m:
            with self.assertRaises(ValueError):m.execute()
            m.capture.assert_not_called()
    def test_25_missing_sixteen_sessions_denies_capture_before_any_reader(self):
        host=NS(protocol=NS(protocol=NS(case_index=9,stopped=False)),scope=NS(sessions=[{}]*15))
        with patch.object(runtime.r.a,'AcceptanceReader')as reader,self.assertRaises(ValueError):runtime.capture_artifacts(NS(),host)
        reader.assert_not_called()
    def test_26_denied_preflight_never_claims_or_executes(self):
        with modeled_main(True,passed=False)as m:
            self.assertEqual(m.code,2);self.assertFalse(m.row['native_claim_created']);m.execute.assert_not_called();m.final.assert_not_called()
    def test_27_observed_preflight_is_not_execution_permission(self):
        with modeled_main(True)as m:
            self.assertEqual(m.code,0);self.assertFalse(m.row['fixed_eight_executed']);m.execute.assert_not_called();m.final.assert_not_called()
    def test_28_failed_execution_prerequisites_do_not_create_claim(self):
        with modeled_main(False,passed=False)as m:
            self.assertEqual(m.code,2);self.assertFalse(m.row['native_claim_created']);m.execute.assert_not_called();m.final.assert_called_once()
    def test_29_missing_current_readiness_cannot_start_execution(self):
        with modeled_main(False,ready_failure=True)as m:
            self.assertEqual(m.code,2);self.assertFalse(m.row['native_claim_created']);m.execute.assert_not_called()
    def test_30_modeled_capture_stays_unqualified_and_uses_new_final_publisher(self):
        with modeled_main(False)as m:
            self.assertEqual(m.code,0);self.assertEqual(m.row['captured_cases'],8);self.assertFalse(m.row['native_startup_qualified'])
            self.assertEqual(m.row['P09_gate'],'OPEN');self.assertFalse(m.row['P10_started']);m.final.assert_called_once()
    def test_31_interrupt_preserves_consumed_claim_and_forbids_retry(self):
        with modeled_main(False,execute_effect=KeyboardInterrupt())as m:
            self.assertEqual(m.code,2);self.assertTrue(m.row['native_claim_created']);self.assertTrue(m.row['rerun_forbidden']);self.assertFalse(m.row['fixed_eight_executed'])
    def test_32_each_worker_stage_keeps_its_own_first_result_notice(self):
        row={};event=dict(state='NATIVE_WORKER_RESULT_RECORDED_BEFORE_CLEANUP',worker_error_code='MODEL_ONLY')
        with patch.object(entry,'publish_small',side_effect=lambda path,value:dict(path=path))as publish,contextlib.redirect_stdout(io.StringIO()):
            for stage in('qualification','fixed_eight','fixed_eight'):entry.notify_stage(stage,event,row)
        self.assertEqual(publish.call_count,2);self.assertIn('qualification_early_worker_notice',row);self.assertIn('fixed_eight_early_worker_notice',row)
        self.assertNotEqual(row['qualification_early_worker_notice'],row['fixed_eight_early_worker_notice'])
    def test_33_cleanup_notice_is_once_per_stage_and_never_a_force_kill_permit(self):
        row={};event=dict(state='WAITING_SAME_OWNED_NATIVE_EXIT_NO_FORCE_KILL',process_id=123)
        with patch.object(entry,'publish_small',side_effect=lambda path,value:dict(path=path))as publish,contextlib.redirect_stdout(io.StringIO()):
            entry.notify_stage('fixed_eight',event,row);entry.notify_stage('fixed_eight',event,row)
        self.assertEqual(publish.call_count,1);self.assertTrue(publish.call_args.args[1]['force_kill_forbidden']);self.assertTrue(publish.call_args.args[1]['rerun_forbidden'])
    def test_34_unknown_notice_stage_is_denied_before_publication(self):
        with patch.object(entry,'publish_small')as publish,self.assertRaises(ValueError):entry.notify_stage('other',{}, {})
        publish.assert_not_called()

if __name__=='__main__':unittest.main()
