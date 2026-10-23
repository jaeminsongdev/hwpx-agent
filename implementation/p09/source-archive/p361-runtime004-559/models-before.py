"""Current004 namespace/manifest/composition contracts; no real Native or file mutations."""
import contextlib,io,itertools,json,unittest
import re
from types import SimpleNamespace as NS
from unittest.mock import Mock,patch
import run_external_crossref_fixed_batch as entry
import crossref_external_batch_runtime as runtime

def manifest_model():
    names=entry.generation_names(current004=True)
    paths=[entry.SELF,'tools/p09/crossref_capture004_worker.py','implementation/p09/tools/crossref-capture004-namespace.ps1']
    pins={p:dict(path=p,bytes=10,sha256='a'*64)for p in paths}
    for p,(size,sha)in runtime.fixed_input_pins(capture004_scope=True).items():pins[p]=dict(path=p,bytes=size,sha256=sha)
    proof=dict(state=entry.CODE_STATE,cleanup=True,fresh_inputs=3,final_fresh_hashes=3,
        contracts=dict(run=25,errors=0,failures=0,skipped=0),source_pins=list(pins.values()),entry_dependency_paths=paths)
    records={names['code']:proof,names['ready']:dict(state='PASS_PUBLIC_ENTRY_PREFLIGHT_AND_FIXED_WORKER_DENIAL_PACKAGE_NOT_NATIVE',
        cleanup=True,code_proof_sha256='b'*64,native_startup_qualified=False,source_pins=list(pins.values()))}
    reader=NS(snapshots={names['code']:dict(path=names['code'],bytes=100,sha256='b'*64)},
        json=Mock(side_effect=lambda p:records[p]),pin=Mock(side_effect=lambda p:pins[p]))
    return reader,records,paths,pins

def modeled_main(preflight,passed):
    class Guard:
        def __init__(self):self.windows=NS();self.samples=[];self.cleanup=False
        def acquire(self):pass
        def check(self,force=False):pass
        def close(self):self.cleanup=True
    shell=dict(path='powershell.exe',bytes=1000,sha256='a'*64);names=entry.generation_names(current004=True)
    def reader(root,check):
        value=NS(snapshots={names['code']:dict(path=names['code'],bytes=1,sha256='b'*64)},final_fresh_hashes=0,
            pin=Mock(return_value=shell),fresh_pin=Mock(return_value=shell))
        def finish():value.final_fresh_hashes=len(value.snapshots)
        value.finish=finish;return value
    patches=[patch.object(entry.r.tools,'select_own_single_cpu',return_value={}),patch.object(entry.r.shared.host,'configure_host_policy'),
        patch.object(entry.r.shared.final,'guard_type',return_value=Guard),patch.object(entry.r.shared.baseline,'guard_type',return_value=Guard),
        patch.object(entry.r.a,'AcceptanceReader',side_effect=reader),patch.object(entry,'load_manifest',return_value=({'external_shell_pins':[shell]},{},set())),
        patch.object(entry.installed,'runtime_pin_matches'),patch.object(entry.installed,'current_identity',return_value={'MODEL_ONLY':True}),
        patch.object(entry.prerequisites,'inspect',return_value={'all_observed_prerequisites_passed':passed}),patch.object(runtime,'absent_attempts'),
        patch.object(runtime,'execute',return_value={'cases':[{}]*8}),patch.object(entry,'publish',return_value={'path':'MODEL_ONLY'}),
        patch.object(entry.Path,'exists',return_value=False),patch.object(entry.Path,'is_symlink',return_value=False),
        patch.object(entry.Path,'is_junction',return_value=False),patch.object(entry.Path,'is_dir',return_value=True),patch.object(entry.Path,'mkdir')]
    mocks=[]
    try:
        mocks=[p.start()for p in patches]
        with contextlib.redirect_stdout(io.StringIO()):status=entry.main(['--preflight-generation-004']if preflight else['--execute-generation-004-fixed-eight'])
        return status,mocks[10],mocks[11].call_args_list,mocks[5],mocks[9]
    finally:
        for p in reversed(patches):p.stop()

def artifact_model(mutation=None):
    sessions=[];traces={};sides={}
    def pin(path):return dict(path=path,bytes=12,sha256='a'*64)
    for index in range(1,9):
        base=runtime.capture004.namespace.directory(index);originals=[];admissions=[]
        for offset,label in enumerate(('save','reopen')):
            native=dict(process_id=100+index*2+offset,process_birth_100ns=123000+index*2+offset,session_id=1,
                cleanup_confirmed=True,assigned_before_initial_thread=True,owner_bound=True)
            identity=dict(process_id=native['process_id'],created_at_utc='MODEL_ONLY')
            sessions.append(dict(startup_profile=native))
            originals.append(dict(label=label,process=identity,quit_invoked=True,close_without_dirty_prompt_returned=True,
                remaining_owned_process_count=0,cleanup_error=None))
            admissions.append(dict(evidence=dict(channel_message_returned=True,observation=dict(compatibility_identity=identity,
                kernel_identity=dict(process_id=native['process_id'],session_id=1),kernel_creation_filetime_100ns=str(native['process_birth_100ns'])))))
        traces[index]=dict(schema_version='hwpx-agent.private.crossref-native-case-trace/v1',source_identity_preserved=True,
            source_sha256=runtime.INPUT_PINS[runtime.SOURCE][1],sessions=originals,
            producer_events=[dict(stage=stage,artifact_sha256='a'*64,artifact_bytes=12,observed_owner_identity=originals[0 if i<2 else 1]['process'])
                for i,stage in enumerate(('opened','saved','reopened'))])
        sides[index]=dict(original_trace=pin(base+'/target-trace.json'),admissions=admissions)
    if mutation:mutation(traces[1],sides[1])
    reader=NS(snapshots={},final_fresh_hashes=0)
    def read_pin(path):
        if '-20261022-g004-'not in path:raise AssertionError('NO_LEGACY_CAPTURE_FALLBACK')
        value=pin(path);reader.snapshots[path]=value;return value
    def read_json(path):
        read_pin(path);index=int(re.search(r'-g004-c([0-9]{2})-',path)[1])
        return traces[index]if path.endswith('target-trace.json')else sides[index]
    def finish():reader.final_fresh_hashes=len(reader.snapshots)
    reader.pin=Mock(side_effect=read_pin);reader.json=Mock(side_effect=read_json);reader.finish=Mock(side_effect=finish)
    host=NS(protocol=NS(protocol=NS(case_index=9,stopped=False)),scope=NS(sessions=sessions))
    return reader,host

class Generation004(unittest.TestCase):
    def test_01_all_four_scopes_are_fixed_and_disjoint(self):
        scopes=[entry.generation_names(),entry.generation_names(True),entry.generation_names(current003=True),entry.generation_names(current004=True)]
        self.assertTrue(all(set(a.values()).isdisjoint(b.values())for a,b in itertools.combinations(scopes,2)))
        self.assertTrue(all(set(a)==set(scopes[0])for a in scopes))
        self.assertTrue(scopes[3]['claim'].endswith('claim004.v1.json'));self.assertTrue(scopes[3]['output'].endswith('run004.v1.json'))
    def test_02_scope_flags_are_typed_mutually_exclusive_not_retry_numbers(self):
        for bad in (0,1,3,'3',None,[]):
            with self.assertRaises(ValueError):entry.generation_names(current004=bad)
        with self.assertRaises(ValueError):entry.generation_names(True,current004=True)
    def test_03_new_public_modes_have_no_retry_selector(self):
        for mode in ('--preflight-generation-004','--execute-generation-004-fixed-eight'):
            args=entry.parser().parse_args([mode]);self.assertIn('004',entry.output_name(args))
            with self.assertRaises(ValueError):entry.output_name(entry.parser().parse_args([mode,'--inspection-run','2']))
    def test_04_new_and_old_modes_are_all_mutually_exclusive(self):
        modes=['--preflight-only','--execute-qualified-fixed-eight','--preflight-generation-002','--execute-generation-002-fixed-eight',
            '--preflight-generation-003','--execute-generation-003-fixed-eight','--preflight-generation-004','--execute-generation-004-fixed-eight']
        with contextlib.redirect_stderr(io.StringIO()):
            for pair in itertools.combinations(modes,2):
                with self.assertRaises(SystemExit):entry.parser().parse_args(list(pair))
    def test_05_no_source_path_case_subset_claim_or_retry_number_is_accepted(self):
        with contextlib.redirect_stderr(io.StringIO()):
            for extra in (['--run','4'],['--cases','1'],['--claim','x.json'],['--source','x.hwpx']):
                with self.assertRaises(SystemExit):entry.parser().parse_args(['--execute-generation-004-fixed-eight',*extra])
    def test_06_new_preflight_does_not_claim_or_execute_even_with_passed_prerequisites(self):
        status,execute,writes,loader,absence=modeled_main(True,True)
        self.assertEqual(status,0);execute.assert_not_called();self.assertEqual(len(writes),1)
        self.assertFalse(writes[0].args[1]['native_claim_created']);self.assertEqual(writes[0].args[1]['generation'],4)
        self.assertEqual(loader.call_args.kwargs,dict(require_runtime_ready=False,current_generation004=True))
        absence.assert_called_once_with(fixed_capture004=True)
    def test_07_denied_prerequisites_cannot_create_claim_or_execute(self):
        status,execute,writes,loader,_=modeled_main(False,False)
        self.assertEqual(status,2);execute.assert_not_called();self.assertEqual(len(writes),1)
        self.assertFalse(writes[0].args[1]['native_claim_created']);self.assertTrue(loader.call_args.kwargs['require_runtime_ready'])
    def test_08_execute_wires_only004_and_claim_precedes_current_invocation(self):
        status,execute,writes,loader,_=modeled_main(False,True)
        self.assertEqual(status,0);self.assertEqual(len(writes),2);self.assertEqual(execute.call_count,1)
        self.assertEqual(writes[0].args[0],entry.generation_names(current004=True)['claim'])
        self.assertTrue(execute.call_args.kwargs['fixed_capture004']);self.assertEqual(writes[1].args[1]['captured_cases'],8)
    def test_09_consumed004_claim_denies_before_loading_or_starting(self):
        claim=entry.generation_names(current004=True)['claim'];loader=Mock()
        with patch.object(entry.Path,'exists',lambda p:p.as_posix().endswith(claim)),patch.object(entry,'load_manifest',loader):
            with self.assertRaisesRegex(ValueError,'ONE_NATIVE_BUNDLE_NO_REPLAY'):entry.main(['--execute-generation-004-fixed-eight'])
        loader.assert_not_called()
    def test_10_original001_and002_outputs_still_cannot_be_replayed(self):
        with patch.object(entry.Path,'exists',return_value=True),patch.object(entry,'load_manifest')as loader:
            for mode in ('--execute-qualified-fixed-eight','--execute-generation-002-fixed-eight','--execute-generation-003-fixed-eight'):
                with self.assertRaisesRegex(ValueError,'IMMUTABLE_OUTPUT'):entry.main([mode])
        loader.assert_not_called()
    def test_11_manifest_binds004_code_and_all_fixed_product_pins(self):
        reader,records,paths,pins=manifest_model()
        with patch.object(entry.r.compact,'unpack',side_effect=lambda p:p),patch.object(entry,'loaded_paths',return_value=set(paths)):
            proof,manifest,all_paths=entry.load_manifest(reader,current_generation004=True)
        self.assertEqual(all_paths,set(paths)|set(runtime.fixed_input_pins(capture004_scope=True)))
        self.assertEqual(reader.json.call_args.args,(entry.generation_names(current004=True)['code'],))
    def test_12_manifest_requires_same004_ready_code_digest(self):
        reader,records,paths,_=manifest_model();records[entry.generation_names(current004=True)['ready']]['code_proof_sha256']='c'*64
        with patch.object(entry.r.compact,'unpack',side_effect=lambda p:p),patch.object(entry,'loaded_paths',return_value=set(paths)):
            with self.assertRaisesRegex(ValueError,'VERIFIED_IMPLEMENTATION_RUNTIME_PACKAGE'):entry.load_manifest(reader,True,current_generation004=True)
    def test_13_changed_worker_source_or_missing_import_cannot_load(self):
        for missing in (False,True):
            reader,_,paths,pins=manifest_model()
            if not missing:reader.pin.side_effect=lambda p:dict(pins[p],sha256='c'*64)
            loaded=set(paths)|({'tools/p09/unpinned004.py'}if missing else set())
            with patch.object(entry.r.compact,'unpack',side_effect=lambda p:p),patch.object(entry,'loaded_paths',return_value=loaded):
                with self.assertRaises(ValueError):entry.load_manifest(reader,current_generation004=True)
    def test_14_wrong_new_probe_pin_denies_even_if_manifest_rows_match(self):
        reader,_,paths,pins=manifest_model();pins[runtime.capture004.namespace.PROBE]['sha256']='c'*64
        with patch.object(entry.r.compact,'unpack',side_effect=lambda p:p),patch.object(entry,'loaded_paths',return_value=set(paths)):
            with self.assertRaisesRegex(ValueError,'FIXED_CURRENT_CAPTURE_INPUTS'):entry.load_manifest(reader,current_generation004=True)
    def test_15_saved_session_success_is_not_required_ready_false(self):
        reader,_,paths,_=manifest_model()
        with patch.object(entry.r.compact,'unpack',side_effect=lambda p:p),patch.object(entry,'loaded_paths',return_value=set(paths)):
            entry.load_manifest(reader,True,current_generation004=True)
        self.assertEqual(reader.json.call_count,2)
    def test_16_scope_and_input_maps_cannot_be_changed_through_returned_values(self):
        value=runtime.fixed_input_pins(capture004_scope=True);value.clear()
        self.assertIn(runtime.capture004.namespace.PROBE,runtime.fixed_input_pins(capture004_scope=True))
        names=entry.generation_names(current004=True);names['claim']='foreign'
        self.assertNotEqual(entry.generation_names(current004=True)['claim'],'foreign')
    def test_17_case_sources_include_current004_program_profile_and_probe(self):
        required=set(runtime.capture004.SOURCES)|{'tools/p09/crossref_capture004_namespace.py','tools/p09/crossref_capture004_worker.py'}
        self.assertLessEqual(required,runtime.CAPTURE004_CASE_PATHS);self.assertLessEqual(runtime.CASE_PATHS,runtime.CAPTURE004_CASE_PATHS)
    def test_18_absence_uses_new_namespace_only_and_keeps_original_refusal(self):
        with patch.object(runtime.capture004.namespace,'require_absent')as fresh:
            runtime.absent_attempts(fixed_capture004=True);fresh.assert_called_once_with(runtime.r.c.ROOT)
        with patch.object(runtime.Path,'exists',return_value=True):
            with self.assertRaisesRegex(ValueError,'EXISTING_CAPTURE_ATTEMPT_NO_REPLAY'):runtime.absent_attempts()
    def test_19_case_boundary_has004_sources_and_one_case_at_a_time(self):
        cases=runtime.CaseInputs(None,{},None,fixed_capture004=True)
        def boundary(guard,manifest,paths,label,shell):
            self.assertEqual(paths,runtime.CAPTURE004_CASE_PATHS)
            return NS(label=label,finish=Mock(),summary=lambda:dict(label=label,closed=True))
        with patch.object(runtime,'Boundary',side_effect=boundary):
            cases.begin(1)
            with self.assertRaises(ValueError):cases.begin(2)
            cases.end(1);cases.begin(2);cases.end(2)
        self.assertEqual([row['label']for row in cases.rows],['case1','case2'])
    def test_20_bad_scope_flags_reject_before_reader_or_worker(self):
        for flag in (0,3,'3',None):
            for call in (lambda:runtime.fixed_input_pins(capture004_scope=flag),lambda:runtime.absent_attempts(fixed_capture004=flag),
                lambda:runtime.CaseInputs(None,{},None,fixed_capture004=flag),lambda:runtime.capture_artifacts(None,None,fixed_capture004=flag),
                lambda:runtime.execute(None,{},set(),None,{},None,{},fixed_capture004=flag)):
                with self.assertRaises(ValueError):call()
    def test_21_missing004_inputs_reject_before_qualifier_or_native(self):
        with patch.object(runtime.candidate,'SessionWorker')as worker:
            with self.assertRaisesRegex(ValueError,'COMPLETE_CAPTURE004_INPUT_CLOSURE'):
                runtime.execute(None,{},set(),None,{},None,{},fixed_capture004=True)
        worker.assert_not_called()
    def test_22_full_composition_selects004_worker_callbacks_and_capture(self):
        class Boundary:
            def __init__(self,*args):self.source=object();self.closed=False;self.fingerprint='a'*64;self.native_pin=Mock();self.shell_pin=Mock()
            def finish(self):self.closed=True
            def summary(self):return {'closed':self.closed}
        guard=NS(windows=object());record={};cases=NS(native_pin=Mock(),begin=Mock(),end=Mock(),rows=[{}]*8,current=None)
        def transport(guard,worker,reader,start,handler,schema,env,notify,attempt):
            attempt['exit_code']=0
            return {}if 'session-worker'in schema else dict(state='fixed_eight_callbacks_returned_semantics_unqualified',completed_callback_cases=8,
                host_messages=152,retained_live_or_uncertain_owners=0,probe_lease_closed=True)
        with contextlib.ExitStack()as stack:
            stack.enter_context(patch.object(runtime,'absent_attempts'));stack.enter_context(patch.object(runtime,'Boundary',Boundary))
            stack.enter_context(patch.object(runtime.installed,'current_identity',return_value={'same':True}))
            stack.enter_context(patch.object(runtime.candidate,'SessionWorker'));stack.enter_context(patch.object(runtime.session,'SessionQualifier'))
            stack.enter_context(patch.object(runtime.io,'run',side_effect=transport));stack.enter_context(patch.object(runtime.batch,'issue_handoff',return_value=NS(consumed=True)))
            stack.enter_context(patch.object(runtime,'CaseInputs',return_value=cases));host=stack.enter_context(patch.object(runtime.batch,'FixedEightHost'))
            fresh=stack.enter_context(patch.object(runtime.capture004,'Fixed004Worker'));old=stack.enter_context(patch.object(runtime.fixed,'FixedWorker'))
            stack.enter_context(patch.object(runtime.session.startup,'parent_without_prompt_kill'))
            capture=stack.enter_context(patch.object(runtime,'capture_artifacts',return_value={'cases':[{}]*8}))
            value=runtime.execute(guard,{},runtime.CAPTURE004_CASE_PATHS,None,{},Mock(),record,fixed_capture004=True)
        self.assertEqual(len(value['cases']),8);self.assertTrue(record['same_invocation_handoff_consumed'])
        fresh.assert_called_once_with(guard);old.assert_not_called();self.assertTrue(capture.call_args.kwargs['fixed_capture004'])
        self.assertIs(host.call_args.args[-2],cases.begin);self.assertIs(host.call_args.args[-1],cases.end)
    def test_23_artifact_binding_still_rejects_partial_sixteen_session_prefix(self):
        host=NS(protocol=NS(protocol=NS(case_index=1,stopped=False)),scope=NS(sessions=[]))
        with self.assertRaisesRegex(ValueError,'ALL_EIGHT_NATIVE_CALLBACKS_AND16_CLOSED_SESSIONS'):runtime.capture_artifacts(None,host,fixed_capture004=True)
    def test_24_all40_artifacts_bind_only004_files_to_original_sixteen_lifetimes(self):
        reader,host=artifact_model()
        with patch.object(runtime.r.a,'AcceptanceReader',return_value=reader):
            result=runtime.capture_artifacts(NS(check=Mock()),host,fixed_capture004=True)
        self.assertEqual((result['fresh_inputs'],result['final_fresh_hashes']),(40,40));self.assertEqual(len(result['cases']),8)
        self.assertFalse(result['crossref_semantics_qualified']);self.assertFalse(result['P09_complete'])
        reader.finish.assert_called_once()
    def test_25_foreign_trace_kernel_lifetime_dirty_cleanup_and_producer_digest_are_rejected(self):
        for mutation in (
            lambda trace,side:side['original_trace'].update(path=runtime.artifact_directory(1)+'/target-trace.json'),
            lambda trace,side:side['admissions'][0]['evidence']['observation'].update(kernel_creation_filetime_100ns='999'),
            lambda trace,side:trace['sessions'][0].update(remaining_owned_process_count=False),
            lambda trace,side:trace['producer_events'][0].update(artifact_sha256='b'*64)):
            reader,host=artifact_model(mutation)
            with patch.object(runtime.r.a,'AcceptanceReader',return_value=reader):
                with self.assertRaises(ValueError):runtime.capture_artifacts(NS(check=Mock()),host,fixed_capture004=True)
            reader.finish.assert_not_called()
    def test_26_consumed003_and_new004_flags_cannot_be_combined(self):
        with self.assertRaises(ValueError):entry.generation_names(current003=True,current004=True)
        for invoke in (lambda:runtime.fixed_input_pins(True,capture004_scope=True),
            lambda:runtime.absent_attempts(fixed_capture003=True,fixed_capture004=True),
            lambda:runtime.CaseInputs(None,{},None,fixed_capture003=True,fixed_capture004=True),
            lambda:runtime.capture_artifacts(None,None,fixed_capture003=True,fixed_capture004=True),
            lambda:runtime.execute(None,{},set(),None,{},None,{},fixed_capture003=True,fixed_capture004=True)):
            with self.assertRaises(ValueError):invoke()
    def test_27_wrong_current004_type_never_reads_manifest(self):
        reader=NS(json=Mock(side_effect=AssertionError('NO_INPUT_READ')))
        for flag in(0,1,4,'4',None,[]):
            with self.assertRaises(ValueError):entry.load_manifest(reader,current_generation004=flag)
        reader.json.assert_not_called()
