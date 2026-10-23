"""Pure010 entry/runtime composition models. No process, claim, actual output or Native starts."""
import contextlib,copy,io,json,unittest
from types import SimpleNamespace as NS
from unittest.mock import Mock,patch
import run_external_crossref_fixed_batch010 as entry
import crossref_external010_runtime as runtime

def manifest_model():
    paths=sorted(runtime.CASE_PATHS|{entry.SELF})
    pins={name:dict(path=name,bytes=10,sha256='a'*64)for name in paths}
    for name,(size,sha)in runtime.fixed_input_pins().items():pins[name]=dict(path=name,bytes=size,sha256=sha)
    proof=dict(state=entry.CODE_STATE,generation=10,cleanup=True,fresh_inputs=3,final_fresh_hashes=3,
        contracts=dict(run=32,errors=0,failures=0,skipped=0),entry_dependency_paths=paths,source_pins=list(pins.values()))
    ready=dict(state=entry.READY_STATE,generation=10,cleanup=True,code_proof_sha256='b'*64,native_startup_qualified=False,source_pins=copy.deepcopy(list(pins.values())))
    records={entry.NAMES['code']:proof,entry.NAMES['ready']:ready}
    reader=NS(snapshots={entry.NAMES['code']:dict(path=entry.NAMES['code'],bytes=1,sha256='b'*64)},
        json=Mock(side_effect=lambda name:entry.layout.pack(records[name])),pin=Mock(side_effect=lambda name:pins[name]))
    return reader,records,pins

class Entry010(unittest.TestCase):
    def test_01_fixed010_paths_never_point_at_consumed_generation(self):
        self.assertEqual(entry.NAMES['output'],entry.publication.OUTPUT)
        for key in('claim','output','preflight','scratch'):self.assertIn('010',entry.NAMES[key])
        self.assertNotIn('run_external_crossref_fixed_batch.py',entry.SELF)
    def test_02_parser_accepts_only_fixed010_modes(self):
        args=entry.parser().parse_args(['--preflight-generation-010']);self.assertTrue(args.preflight_generation_010)
        self.assertTrue(entry.parser().parse_args(['--execute-generation-010-fixed-eight']).execute_generation_010_fixed_eight)
    def test_03_old_generations_subsets_paths_retry_and_conflicting_modes_are_denied(self):
        for args in([],['--execute-generation-004-fixed-eight'],['--generation','5'],['--case','1'],['--retry'],
            ['--preflight-generation-010','--execute-generation-010-fixed-eight']):
            with contextlib.redirect_stderr(io.StringIO()),self.assertRaises(SystemExit):entry.parser().parse_args(args)
    def test_04_current_code_manifest_and_fixed_inputs_are_checked(self):
        reader,_,_=manifest_model()
        with patch.object(entry,'loaded_paths',return_value={entry.SELF}):
            proof,pins,paths=entry.load_manifest(reader)
        self.assertEqual(proof['generation'],10);self.assertTrue(runtime.CASE_PATHS<=paths);self.assertTrue(set(runtime.fixed_input_pins())<=paths)
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
    def test_16_boundary_reuses_original_host_image_guard_and_adds_exact010_probe(self):
        def init(obj,*args,**kwargs):obj.source=NS(snapshots={runtime.capture.namespace.PROBE:dict(bytes=runtime.capture.PROBE_PIN[0],sha256=runtime.capture.PROBE_PIN[1])})
        with patch.object(runtime.original.Boundary,'__init__',autospec=True,side_effect=init)as old:
            runtime.Boundary(NS(),{},set(),'MODEL010',{})
        self.assertTrue(old.call_args.kwargs['current004'])
    def test_17_wrong010_probe_cannot_pass_even_with_a_manifest(self):
        def init(obj,*args,**kwargs):obj.source=NS(snapshots={runtime.capture.namespace.PROBE:dict(bytes=1,sha256='0'*64)})
        with patch.object(runtime.original.Boundary,'__init__',autospec=True,side_effect=init),self.assertRaises(ValueError):runtime.Boundary(NS(),{},set(),'MODEL010',{})
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
    def test_25_missing_sixteen_sessions_denies_capture_before_any_reader(self):
        host=NS(protocol=NS(protocol=NS(case_index=9,stopped=False)),scope=NS(sessions=[{}]*15))
        with patch.object(runtime.r.a,'AcceptanceReader')as reader,self.assertRaises(ValueError):runtime.capture_artifacts(NS(),host)
        reader.assert_not_called()
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
