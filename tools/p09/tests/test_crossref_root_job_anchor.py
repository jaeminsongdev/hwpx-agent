"""New readonly root-boundary contracts only, never a native launch."""
import ast
import copy
import io
import json
from pathlib import Path
import sys
from types import SimpleNamespace as NS
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'tools/p09'))
import crossref_root_job_anchor as root


class RootBoundaryContracts(unittest.TestCase):
    actual=[]

    def test_01_only_explicit_existing_parent_permission_never_owned_job_escape(self):
        for value in (dict(job_present=True,query_succeeded=True,flags=0x2238),
                dict(job_present=True,query_succeeded=False,flags=0x2800),
                dict(job_present=True,query_succeeded=True,flags=0x1000)):
            with patch.object(root.host,'read_parent_cpu',return_value=value):
                with self.assertRaisesRegex(ValueError,'PARENT_BREAKAWAY_NOT_ALLOWED_NO_FALLBACK'):
                    root.permitted_external_parent(None)
        for value in (dict(job_present=True,query_succeeded=True,flags=0x2800),dict(job_present=False)):
            with patch.object(root.host,'read_parent_cpu',return_value=value):
                self.assertEqual(root.permitted_external_parent(None),value)

    def test_02_closed_child_no_generic_launch_com_or_force_termination(self):
        text=(ROOT/'tools/p09/crossref_root_job_anchor.py').read_text(encoding='utf-8')
        tree=ast.parse(text)
        calls=[n.func.attr if isinstance(n.func,ast.Attribute) else n.func.id for n in ast.walk(tree)
            if isinstance(n,ast.Call) and isinstance(n.func,(ast.Name,ast.Attribute))]
        self.assertFalse(set(calls)&{'Popen','system','TerminateJobObject','TerminateProcess','kill','CoCreateInstance'})
        self.assertFalse(any(isinstance(n,ast.If) and '__name__' in ast.unparse(n.test) for n in tree.body))
        self.assertNotIn('HWPFrame.',text);self.assertNotIn('-Automation',text)
        self.assertIn('fixed.fixed_command(self.owner_job.plan)',text)
        self.assertIn('MEASURED_ALL_ANCESTOR_JOBS_REMOVED',text)
        self.assertEqual(root.FLAGS,0x09004004)

    def test_03_live_child_and_retry_refusal_preserve_handles_without_sampling(self):
        state=root.ReadonlyRootAnchor.__new__(root.ReadonlyRootAnchor)
        state.closed=False;state.start_attempted=True;state.resume_attempted=True
        state.process=101;state.thread=102;state.owner_job=NS(job=103)
        state.windows=NS(k=NS(WaitForSingleObject=lambda h,t:258))
        with self.assertRaisesRegex(ValueError,'NO_START_RETRY'):state.create_suspended()
        with self.assertRaisesRegex(ValueError,'NO_RESUME_RETRY'):state.resume_readonly()
        with self.assertRaisesRegex(ValueError,'LIVE_READONLY_CHILD_RETAIN_HANDLES'):state.close()
        self.assertEqual((state.process,state.thread,state.owner_job.job),(101,102,103))

    def test_04_actual_owned_guard_job_refuses_breakaway_before_any_child(self):
        windows=root.limits.c.Windows()
        state=root.ReadonlyRootAnchor(windows,lambda:None,
            lambda:(_ for _ in ()).throw(ValueError('TEST_RUNTIME_PIN_MUST_NOT_REACH')))
        try:
            with self.assertRaisesRegex(ValueError,'PARENT_BREAKAWAY_NOT_ALLOWED_NO_FALLBACK') as caught:
                state.create_suspended()
            self.assertIs(caught.exception.readonly_root_anchor,state)
            self.assertFalse(state.created);self.assertIsNone(state.process);self.assertIsNone(state.thread)
        finally:state.close()
        self.actual.append(copy.deepcopy(state.profile))

    def test_05_model_denied_fixed_body_cleanup_preserves_failure_without_guard_or_retry(self):
        state=root.ReadonlyRootAnchor.__new__(root.ReadonlyRootAnchor)
        state.start_failed=True;state.created=True;state.closed=False;state.resume_attempted=False
        state.resume_call_attempted=False
        state.process=101;state.thread=102;state.profile={'start_error_code':'XREF_ROOT_ANCHOR_MEASURED_ALL_ANCESTOR_JOBS_REMOVED'}
        state._handle=lambda suspended:None
        state.owner_job=NS(_private_bytes=lambda process:4096)
        def code(handle,pointer):
            root.ctypes.cast(pointer,root.ctypes.POINTER(root.w.DWORD)).contents.value=65;return True
        state.windows=NS(memory_limit=32*1024**2,k=NS(ResumeThread=lambda h:1,
            WaitForSingleObject=lambda h,t:0,GetExitCodeProcess=code))
        state.checkpoint=lambda:(_ for _ in ()).throw(ValueError('STOP_MODEL_PRESSURE'))
        self.assertEqual(state.finish_failed_readonly(),65)
        self.assertEqual(state.profile['start_error_code'],'XREF_ROOT_ANCHOR_MEASURED_ALL_ANCESTOR_JOBS_REMOVED')
        self.assertFalse(state.profile['root_established']);self.assertTrue(state.profile['failed_readonly_cleanup_only'])
        with self.assertRaisesRegex(ValueError,'FAILED_FIXED_READONLY_CLEANUP_ONLY'):state.finish_failed_readonly()


if __name__=='__main__':
    result=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(RootBoundaryContracts))
    failures=[dict(test=t.id(),last_line=trace.splitlines()[-1][:160]) for t,trace in result.errors+result.failures]
    print(json.dumps(dict(state='five_closed_root_boundary_contracts_pass_no_native' if result.wasSuccessful()
        else 'closed_root_boundary_contract_failed',passed=result.testsRun-len(failures),failed=len(failures),
        declared=result.testsRun,failures=failures,actual_owned_job_denials=RootBoundaryContracts.actual,
        actual_Hangul_or_COM=False,prior_suites_reexecuted=False,native_execution_authorized=False,
        native_startup_qualified=False,p09_complete=False)))
    raise SystemExit(0 if result.wasSuccessful() else 2)
