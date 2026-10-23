"""New first-instruction Job contracts only; no existing suite replay."""
import ast
import copy
import ctypes
import io
import json
from pathlib import Path
import sys
from types import SimpleNamespace as NS
import unittest

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'tools/p09'))
import accept_case112_current_epoch as a
import crossref_preassigned_readonly as atomic


class PreassignedContracts(unittest.TestCase):
    actual=[]

    def test_01_arbitrary_roles_rejected_before_runtime_or_command(self):
        for role in ('native','execute','hwp',True,None,'limit_selfcheck;execute'):
            with self.assertRaisesRegex(ValueError,'FIXED_READONLY_ROLE'):
                atomic.fixed_command({},role)

    def test_02_atomic_creation_no_late_assignment_fallback_or_kill(self):
        source=(ROOT/'tools/p09/crossref_preassigned_readonly.py').read_text(encoding='utf-8')
        calls=[n.func.attr if isinstance(n.func,ast.Attribute) else n.func.id
            for n in ast.walk(ast.parse(source)) if isinstance(n,ast.Call)
            and isinstance(n.func,(ast.Name,ast.Attribute))]
        self.assertFalse(set(calls)&{'AssignProcessToJobObject','TerminateJobObject','TerminateProcess','Popen','kill','system'})
        self.assertEqual(atomic.JOB_LIST,0x2000d)
        self.assertEqual(atomic.CREATE_FLAGS,0x08084004)
        self.assertNotIn('-ExecuteNative',source)
        self.assertNotIn('HWPFrame.',source)
        compile(atomic.CHILD,'<fixed-readonly-limit-selfcheck>','exec')
        self.assertEqual(ctypes.sizeof(atomic.ProcessInfo),ctypes.sizeof(ctypes.c_void_p)*2+8)
        self.assertGreater(ctypes.sizeof(atomic.StartupInfoEx),ctypes.sizeof(atomic.StartupInfo))

    def test_03_retries_refused_before_any_api(self):
        process=atomic.PreassignedReadonlyProcess.__new__(atomic.PreassignedReadonlyProcess)
        process.closed=False;process.creation_attempted=True
        with self.assertRaisesRegex(ValueError,'NO_CREATION_RETRY'):process.create_suspended()
        process.profile={'suspended_handle_verified':True};process.resume_attempted=True
        with self.assertRaisesRegex(ValueError,'NO_RESUME_RETRY'):process.resume_readonly()

    def test_04_live_close_retains_all_handles_and_skips_sampler(self):
        process=atomic.PreassignedReadonlyProcess.__new__(atomic.PreassignedReadonlyProcess)
        process.closed=False;process.process=101;process.thread=102
        process.envelope=NS(job=103)
        process.windows=NS(k=NS(WaitForSingleObject=lambda p,t:258))
        with self.assertRaisesRegex(ValueError,'LIVE_CHILD_RETAIN_HANDLES'):process.close()
        self.assertEqual((process.process,process.thread,process.envelope.job),(101,102,103))

    def test_05_actual_child_is_preassigned_and_selfchecks_then_exits_cleanly(self):
        # The enclosing original supervisor is the sole resource sampler.
        runtime_reader=a.AcceptanceReader(atomic.PYTHON.parent,lambda:None)
        pin=runtime_reader.pin(atomic.PYTHON.name)
        process=atomic.PreassignedReadonlyProcess(atomic.host.c.Windows(),lambda:None)
        try:
            process.create_suspended()
            self.assertTrue(process.profile['suspended_handle_verified'])
            self.assertEqual(process.profile['pre_run_user_cpu_100ns'],0)
            self.assertEqual(process.windows.accounting(process.envelope.job)['active_processes'],1)
            with self.assertRaisesRegex(ValueError,'LIVE_CHILD_RETAIN_HANDLES'):process.close()
            process.resume_readonly()
            self.assertEqual(process.wait_readonly(),0)
            runtime_reader.finish()
            self.assertEqual(runtime_reader.final_fresh_hashes,1)
        finally:
            process.close()
        profile=copy.deepcopy(process.profile)
        profile['runtime_pin']=pin
        profile['runtime_root']=str(runtime_reader.root)
        profile['runtime_source_reads']={'fresh':1,'final':runtime_reader.final_fresh_hashes}
        self.actual.append(profile)


if __name__=='__main__':
    result=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(PreassignedContracts))
    failures=[dict(test=t.id(),last_line=trace.splitlines()[-1][:160]) for t,trace in result.errors+result.failures]
    print(json.dumps(dict(state='five_job_at_creation_readonly_contracts_pass_not_native' if result.wasSuccessful()
        else 'job_at_creation_readonly_contract_failed',passed=result.testsRun-len(failures),failed=len(failures),
        declared=result.testsRun,failures=failures,actual_preassigned_profiles=PreassignedContracts.actual,
        prior_suites_reexecuted=False,actual_Hangul_or_COM=False,native_startup_qualified=False,
        native_execution_authorized=False,p09_complete=False)))
    raise SystemExit(0 if result.wasSuccessful() else 2)
