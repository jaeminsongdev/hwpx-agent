"""New fixed namespace/manifest models only. No Native, file writes or old execution replay."""
import contextlib,io,itertools,unittest
from types import SimpleNamespace as NS
from unittest.mock import Mock,patch
import run_external_crossref_fixed_batch as entry
import crossref_external_batch_runtime as runtime

def modeled(preflight,passed):
    class Guard:
        def __init__(self):self.windows=NS();self.samples=[];self.cleanup=False
        def acquire(self):pass
        def check(self,force=False):pass
        def close(self):self.cleanup=True
    def reader(root,check):
        names=entry.generation_names(True);shell=dict(path='powershell.exe',bytes=1000,sha256='a'*64)
        r=NS(snapshots={names['code']:dict(path=names['code'],bytes=1,sha256='b'*64)},final_fresh_hashes=0)
        r.pin=Mock(return_value=shell);r.fresh_pin=Mock(return_value=shell)
        def finish():r.final_fresh_hashes=len(r.snapshots)
        r.finish=finish;return r
    patches=[patch.object(entry.r.tools,'select_own_single_cpu',return_value={}),patch.object(entry.r.shared.host,'configure_host_policy'),
        patch.object(entry.r.shared.final,'guard_type',return_value=Guard),patch.object(entry.r.shared.baseline,'guard_type',return_value=Guard),
        patch.object(entry.r.a,'AcceptanceReader',side_effect=reader),patch.object(entry,'load_manifest',return_value=({'external_shell_pins':[dict(path='powershell.exe',bytes=1000,sha256='a'*64)]},{},set())),
        patch.object(entry.installed,'runtime_pin_matches'),patch.object(entry.installed,'current_identity',return_value={'MODEL_ONLY':True}),
        patch.object(entry.prerequisites,'inspect',return_value={'all_observed_prerequisites_passed':passed}),patch.object(runtime,'absent_attempts'),
        patch.object(runtime,'execute'),patch.object(entry,'publish',return_value={'path':'MODEL_ONLY'}),patch.object(entry.Path,'exists',return_value=False),patch.object(entry.Path,'is_symlink',return_value=False)]
    mocks=[]
    try:
        mocks=[p.start()for p in patches]
        with contextlib.redirect_stdout(io.StringIO()):status=entry.main(['--preflight-generation-002']if preflight else['--execute-generation-002-fixed-eight'])
        return status,mocks[10],mocks[11].call_args_list,mocks[5]
    finally:
        for p in reversed(patches):p.stop()

def manifest_model(ready=False):
    paths=[entry.SELF,'tools/p09/crossref_startup_input_idle.py'];pins=[dict(path=p,bytes=10,sha256='a'*64)for p in paths]
    names=entry.generation_names(True);digest='b'*64
    proof=dict(state=entry.CODE_STATE,cleanup=True,fresh_inputs=2,final_fresh_hashes=2,contracts=dict(run=23,errors=0,failures=0,skipped=0),source_pins=pins,entry_dependency_paths=paths)
    records={names['code']:proof,names['ready']:dict(state='PASS_PUBLIC_ENTRY_PREFLIGHT_AND_FIXED_WORKER_DENIAL_PACKAGE_NOT_NATIVE',cleanup=True,
        code_proof_sha256=digest,native_startup_qualified=False,source_pins=pins)}
    reader=NS(snapshots={names['code']:dict(path=names['code'],bytes=100,sha256=digest)},json=Mock(side_effect=lambda p:records[p]),
        pin=Mock(side_effect=lambda p:next(x for x in pins if x['path']==p)))
    return reader,records,paths

class Tests(unittest.TestCase):
    def test_new_namespace_is_disjoint_and_keeps_exact_old_names(self):
        old,new=entry.generation_names(),entry.generation_names(True)
        self.assertEqual(old['claim'],entry.CLAIM);self.assertEqual(old['output'],entry.OUTPUT)
        self.assertEqual(set(old),set(new));self.assertTrue(set(old.values()).isdisjoint(new.values()))
        self.assertTrue(new['claim'].endswith('claim002.v1.json'));self.assertTrue(new['output'].endswith('run002.v1.json'))
    def test_generation_flag_is_typed_not_retry_number(self):
        for value in(0,1,2,'2',None,[]):
            with self.assertRaises(ValueError):entry.generation_names(value)
    def test_new_preflight_is_single_fixed_namespace_without_retry_selector(self):
        a=entry.parser().parse_args(['--preflight-generation-002']);self.assertIn('generation002-preflight',entry.output_name(a))
        with self.assertRaises(ValueError):entry.output_name(entry.parser().parse_args(['--preflight-generation-002','--inspection-run','2']))
    def test_new_execution_is_single_fixed_namespace_without_retry_selector(self):
        a=entry.parser().parse_args(['--execute-generation-002-fixed-eight']);self.assertEqual(entry.output_name(a),entry.generation_names(True)['output'])
        with self.assertRaises(ValueError):entry.output_name(entry.parser().parse_args(['--execute-generation-002-fixed-eight','--inspection-run','2']))
    def test_no_arbitrary_number_case_subset_or_user_paths(self):
        with contextlib.redirect_stderr(io.StringIO()):
            for extra in(['--run','3'],['--cases','1'],['--claim','other.json'],['--source','other.hwpx']):
                with self.assertRaises(SystemExit):entry.parser().parse_args(['--execute-generation-002-fixed-eight',*extra])
    def test_all_old_and_new_modes_are_mutually_exclusive(self):
        modes=['--preflight-only','--execute-qualified-fixed-eight','--preflight-generation-002','--execute-generation-002-fixed-eight']
        with contextlib.redirect_stderr(io.StringIO()):
            for pair in itertools.combinations(modes,2):
                with self.assertRaises(SystemExit):entry.parser().parse_args(list(pair))
    def test_startup_idle_helper_is_fresh_in_every_case_boundary(self):
        self.assertIn('tools/p09/crossref_startup_input_idle.py',runtime.CASE_PATHS)
        self.assertIn('crossref_startup_input_idle',runtime.CASE_PY)
    def test_source_and_fixed_eight_paths_do_not_change_with_new_namespace(self):
        self.assertEqual(len({runtime.artifact_directory(i)for i in range(1,9)}),8)
        for index in(0,9,True):
            with self.assertRaises(ValueError):runtime.artifact_directory(index)
    def test_current_manifest_uses_new_code_without_old_authority(self):
        reader,records,paths=manifest_model()
        with patch.object(entry.r.compact,'unpack',side_effect=lambda p:p),patch.object(entry,'loaded_paths',return_value=set(paths)),patch.object(runtime,'INPUT_PINS',{}):
            proof,manifest,all_paths=entry.load_manifest(reader,current_generation002=True)
        self.assertEqual(all_paths,set(paths));reader.json.assert_called_once_with(entry.generation_names(True)['code'])
    def test_current_manifest_requires_exact_new_ready_code_digest(self):
        reader,records,paths=manifest_model()
        with patch.object(entry.r.compact,'unpack',side_effect=lambda p:p),patch.object(entry,'loaded_paths',return_value=set(paths)),patch.object(runtime,'INPUT_PINS',{}):
            entry.load_manifest(reader,require_runtime_ready=True,current_generation002=True)
        self.assertEqual(reader.json.call_count,2)
    def test_changed_active_dependency_is_rejected(self):
        reader,records,paths=manifest_model();reader.pin.side_effect=lambda p:dict(path=p,bytes=10,sha256='c'*64)
        with patch.object(entry.r.compact,'unpack',side_effect=lambda p:p),patch.object(entry,'loaded_paths',return_value=set(paths)),patch.object(runtime,'INPUT_PINS',{}):
            with self.assertRaisesRegex(ValueError,'CURRENT_ENTRY_CODE_CHANGED_REQUALIFY'):entry.load_manifest(reader,current_generation002=True)
    def test_missing_new_helper_is_not_accepted_as_closed_inputs(self):
        reader,records,paths=manifest_model();extra=set(paths)|{'tools/p09/new_unpinned_helper.py'}
        with patch.object(entry.r.compact,'unpack',side_effect=lambda p:p),patch.object(entry,'loaded_paths',return_value=extra),patch.object(runtime,'INPUT_PINS',{}):
            with self.assertRaisesRegex(ValueError,'COMPLETE_CURRENT_ENTRY_IMPORT_SOURCE_MANIFEST'):entry.load_manifest(reader,current_generation002=True)
    def test_wrong_ready_generation_does_not_authorize_execution(self):
        reader,records,paths=manifest_model();records[entry.generation_names(True)['ready']]['code_proof_sha256']='c'*64
        with patch.object(entry.r.compact,'unpack',side_effect=lambda p:p),patch.object(entry,'loaded_paths',return_value=set(paths)),patch.object(runtime,'INPUT_PINS',{}):
            with self.assertRaisesRegex(ValueError,'VERIFIED_IMPLEMENTATION_RUNTIME_PACKAGE_REQUIRED_NOT_NATIVE_PERMIT'):entry.load_manifest(reader,True,True)
    def test_new_public_preflight_never_claims_or_executes_even_if_prerequisites_pass(self):
        status,execute,writes,loader=modeled(True,True)
        self.assertEqual(status,0);execute.assert_not_called();self.assertEqual(len(writes),1)
        self.assertFalse(writes[0].args[1]['native_claim_created']);self.assertEqual(writes[0].args[1]['generation'],2)
        self.assertFalse(loader.call_args.kwargs['require_runtime_ready']);self.assertTrue(loader.call_args.kwargs['current_generation002'])
    def test_new_execution_with_denied_prerequisites_never_creates_claim(self):
        status,execute,writes,loader=modeled(False,False)
        self.assertEqual(status,2);execute.assert_not_called();self.assertEqual(len(writes),1);self.assertFalse(writes[0].args[1]['native_claim_created'])
        self.assertTrue(loader.call_args.kwargs['require_runtime_ready'])
    def test_reused_current_claim_is_rejected_before_loading_or_native(self):
        claim=entry.generation_names(True)['claim'];loader=Mock()
        def exists(path):return path.as_posix().endswith(claim)
        with patch.object(entry.Path,'exists',exists),patch.object(entry,'load_manifest',loader):
            with self.assertRaisesRegex(ValueError,'EXTERNAL_ENTRY_ONE_NATIVE_BUNDLE_NO_REPLAY'):entry.main(['--execute-generation-002-fixed-eight'])
        loader.assert_not_called()
    def test_old_consumed_output_still_refuses_execution_before_loading(self):
        loader=Mock()
        with patch.object(entry.Path,'exists',return_value=True),patch.object(entry,'load_manifest',loader):
            with self.assertRaisesRegex(ValueError,'EXTERNAL_ENTRY_IMMUTABLE_OUTPUT'):entry.main(['--execute-qualified-fixed-eight'])
        loader.assert_not_called()
    def test_fixed_names_cannot_be_changed_by_mutating_a_previous_result(self):
        first=entry.generation_names(True);first['claim']='other.json'
        self.assertNotEqual(entry.generation_names(True)['claim'],first['claim'])
