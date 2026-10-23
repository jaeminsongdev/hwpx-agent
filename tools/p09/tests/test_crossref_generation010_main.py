"""Pure010 entry/runtime composition models. No process, claim, actual output or Native starts."""
import contextlib,copy,io,json,unittest
from types import SimpleNamespace as NS
from unittest.mock import Mock,patch
import run_external_crossref_fixed_batch010 as entry
import crossref_external010_runtime as runtime

@contextlib.contextmanager
def modeled_main(preflight,passed=True,ready_failure=False,execute_effect=None,final_failure=False):
    class Guard:
        def __init__(self):self.windows=NS();self.samples=[];self.cleanup=False
        def acquire(self):pass
        def check(self,force=False):pass
        def close(self):self.cleanup=True
        def advance(self,label,closed):entry.runtime.require(closed()is True,'MODEL_CLOSED_BOUNDARY')
        def complete(self,closed,**kwargs):entry.runtime.require(closed()is True,'MODEL_COMPLETION')
        def section_summary(self):return {'MODEL_ONLY':True}
    shell=dict(path='powershell.exe',bytes=100,sha256='a'*64)
    def reader(root,check):
        value=NS(root=root,snapshots={entry.NAMES['code']:dict(path=entry.NAMES['code'],bytes=1,sha256='b'*64)},final_fresh_hashes=0,
            pin=Mock(return_value=shell),fresh_pin=Mock(return_value=shell))
        def finish():value.final_fresh_hashes=len(value.snapshots)
        def pin(name):
            if name not in value.snapshots:value.snapshots[name]=dict(path=name,bytes=100,sha256='a'*64)
            return value.snapshots[name]
        value.pin=Mock(side_effect=pin);value.fresh_pin=value.pin;value.finish=finish;return value
    def execution(*args):
        if execute_effect is not None:raise execute_effect
        args[-1]['batch_closed_for_final_audit']=True
        return {'cases':[{}]*8}
    patches=[patch.object(entry.r.tools,'select_own_single_cpu',return_value={}),patch.object(entry.r.shared.host,'configure_host_policy'),
        patch.object(entry,'make_guard',side_effect=Guard),
        patch.object(entry.r.a,'AcceptanceReader',side_effect=reader),patch.object(entry,'load_manifest',
            side_effect=ValueError('MODEL_READY_MISSING')if ready_failure else None,return_value=({'external_shell_pins':[shell]},{},set())),
        patch.object(entry.host_profile,'require_qualification',return_value={'MODEL_ONLY':True}),
        patch.object(entry.host_profile,'verify_current_reader',return_value={'MODEL_ONLY':True}),
        patch.object(entry.installed,'current_identity',return_value={'MODEL_CREATOR':True}),
        patch.object(entry.prerequisites,'inspect',return_value={'all_observed_prerequisites_passed':passed}),
        patch.object(runtime,'absent_attempts'),patch.object(runtime,'execute',side_effect=execution),
        patch.object(entry,'publish_small',side_effect=lambda path,row:dict(path=path,bytes=1,sha256='a'*64)),
        patch.object(entry.publication,'publish_final',return_value={'path':'MODEL_FINAL_ONLY'}),
        patch.object(entry.Path,'exists',return_value=False),patch.object(entry.Path,'is_symlink',return_value=False),
        patch.object(entry.Path,'is_junction',return_value=False),patch.object(entry.Path,'is_dir',return_value=True),patch.object(entry.Path,'mkdir')]
    if final_failure:patches.append(patch.object(entry,'final_readers',side_effect=ValueError('MODEL_FINAL_AUDIT_FAILED')))
    with contextlib.ExitStack()as stack:
        mocks=[stack.enter_context(p)for p in patches];output=io.StringIO()
        with contextlib.redirect_stdout(output):code=entry.main(['--preflight-generation-010']if preflight else['--execute-generation-010-fixed-eight'])
        final=entry.publication.publish_final.call_args.args[1]if not preflight else entry.publish_small.call_args.args[1]
        yield NS(code=code,row=final,mocks=mocks,publish=entry.publish_small,final=entry.publication.publish_final,
            execute=runtime.execute,load=entry.load_manifest,stdout=output.getvalue())

class Main010(unittest.TestCase):
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

    def test_35_model_whole_preparation_and_final_audit_both_close(self):
        with modeled_main(False)as m:
            self.assertTrue(entry.sections.closed_boundary(m.row['preparation_boundary']))
            self.assertTrue(entry.sections.closed_boundary(m.row['final_audit_boundary']))
    def test_36_prerequisite_denial_is_a_publishable_failed_nonclaim_not_an_unknown_state(self):
        with modeled_main(False,passed=False)as m:
            self.assertEqual(m.row['state'],'FAILED_EXTERNAL_QUALIFIED_ENTRY')
            entry.publication.validate(m.row)

    def test_37_final_audit_failure_cannot_leave_captured_state_or_success_exit(self):
        with modeled_main(False,final_failure=True)as m:
            self.assertEqual(m.code,2);self.assertEqual(m.row['state'],'FAILED_EXTERNAL_QUALIFIED_ENTRY')
            self.assertTrue(m.row['native_claim_created']);self.assertTrue(m.row['fixed_eight_executed'])
            self.assertEqual(m.row['accepted_count_delta'],0);self.assertNotIn('final_fresh_hashes',m.row)
            entry.publication.validate(m.row)

if __name__=='__main__':unittest.main()
