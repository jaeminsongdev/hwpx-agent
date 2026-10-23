"""New host-envelope tests only; no native target or replay of prior channel tests."""
import ast
import copy
import io
import json
from pathlib import Path
import subprocess
import sys
import time
from types import SimpleNamespace as NS
import unittest

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'tools/p09'))
import crossref_owned_host_process as host
import accept_case112_current_epoch as a
from bounded_process_progress import BoundedProcessCapture


def drain_readonly(process, capture, maximum):
    # This deadline covers ONLY the frozen readonly qualification target, never Hancom.
    end=time.monotonic()+maximum;peak=0
    while True:
        if time.monotonic()>=end:raise ValueError('READONLY_HOST_TEST_DEADLINE')
        info=process.observe();peak=max(peak,info['active_processes'])
        try:
            output,error=capture.communicate(timeout=.5)
            return output,error,peak
        except subprocess.TimeoutExpired:capture.progress()


class OwnedHostContracts(unittest.TestCase):
    actual=[]

    def test_01_worker_partition_and_native_partition_fit_original_job_budget(self):
        total=32*1024**3
        windows=NS(processors=16,mask=1,cpu_rate=625,total_ram=total,memory_limit=total*8//100//4096*4096)
        native=host.native.validate_plan(windows);worker=host.host_plan(windows)
        self.assertLessEqual(native['memory_limit']+worker['memory_limit'],windows.memory_limit)
        self.assertEqual(worker['affinity'],native['affinity'])
        self.assertEqual(worker['cpu_rate'],native['cpu_rate'])
        self.assertEqual(worker['flags'] & (0x2000|0x1800|0x2|0x4),0)

    def test_02_fixed_readonly_target_has_no_native_or_force_kill_route(self):
        source=(ROOT/'tools/p09/crossref_owned_host_process.py').read_text(encoding='utf-8')
        tree=ast.parse(source)
        calls=[n.func.attr if isinstance(n.func,ast.Attribute) else n.func.id for n in ast.walk(tree)
            if isinstance(n,ast.Call) and isinstance(n.func,(ast.Name,ast.Attribute))]
        self.assertFalse(set(calls) & {'TerminateJobObject','TerminateProcess','kill','system'})
        self.assertFalse(hasattr(host.OwnedHostProcess,'kill'))
        self.assertIn("'-WrapperOnly'",source)
        self.assertNotIn('-ExecuteNative',source)
        self.assertFalse(any(isinstance(n,ast.If) and '__name__' in ast.unparse(n.test) for n in tree.body))

    def test_03_live_worker_close_refuses_without_losing_job(self):
        state=host.OwnedHostProcess.__new__(host.OwnedHostProcess)
        state.closed=False;state.job=123;state.process=NS(poll=lambda:None)
        state.profile=dict(cleanup_confirmed=False)
        with self.assertRaisesRegex(ValueError,'LIVE_WORKER_NO_FORCE_CLOSE'):state.close()
        self.assertEqual(state.job,123)
        self.assertFalse(state.closed)

    def test_04_live_tree_close_refuses_after_bootstrap_exit(self):
        state=host.OwnedHostProcess.__new__(host.OwnedHostProcess)
        state.closed=False;state.job=123;state.process=NS(poll=lambda:0)
        state.profile=dict(cleanup_confirmed=False)
        state.windows=NS(accounting=lambda j:dict(active_processes=1))
        with self.assertRaisesRegex(ValueError,'LIVE_TREE_NO_FORCE_CLOSE'):state.close()
        self.assertEqual(state.job,123)

    def test_05_start_and_signal_are_one_attempt_not_retry_permits(self):
        state=host.OwnedHostProcess.__new__(host.OwnedHostProcess)
        state.closed=False;state.start_attempted=True;state.process=None
        with self.assertRaisesRegex(ValueError,'NO_WORKER_RESTART'):state.start_waiting(None)
        with self.assertRaisesRegex(ValueError,'NO_TARGET_SIGNAL_RETRY'):state.signal_readonly_target()

    def test_06_actual_empty_one_percent_job_limits_and_close(self):
        windows=host.c.Windows();state=host.OwnedHostProcess(windows,lambda:None)
        try:
            readback=state.readback()
            self.assertTrue(readback['verified'])
            self.assertFalse(readback['kill_on_close'] or readback['time_limit_installed'])
            self.assertLessEqual(readback['job_private_limit_mib']*1048576,windows.memory_limit//8)
            self.assertEqual(state.observe()['active_processes'],0)
        finally:state.close()
        self.actual.append(copy.deepcopy(state.profile))

    def test_07_actual_eof_before_signal_never_launches_readonly_target(self):
        windows=host.c.Windows();state=host.OwnedHostProcess(windows,lambda:None)
        reader=a.AcceptanceReader(ROOT,lambda:None);capture=None
        try:
            state.start_waiting(reader)
            self.assertTrue(state.profile['bootstrap_assigned'] and state.profile['bootstrap_limits_readback'])
            state.cancel_before_signal()
            capture=BoundedProcessCapture(state,output_limit=4096,parse_markers=False)
            output,error,peak=drain_readonly(state,capture,10)
            self.assertEqual(state.returncode,125)
            self.assertEqual(output,'');self.assertEqual(error,'')
            self.assertFalse(state.profile['readonly_signal_written'])
            reader.finish()
            self.assertEqual(reader.final_fresh_hashes,len(reader.snapshots))
            state.profile['qualification_source_reads']=dict(fresh=len(reader.snapshots),final=reader.final_fresh_hashes)
        finally:
            if capture is not None:capture.close()
            state.close()
        self.actual.append(copy.deepcopy(state.profile))

    def test_08_actual_fixed_wrapper_target_runs_in_one_percent_host_job(self):
        windows=host.c.Windows();state=host.OwnedHostProcess(windows,lambda:None)
        reader=a.AcceptanceReader(ROOT,lambda:None);capture=None
        try:
            state.start_waiting(reader);state.signal_readonly_target()
            capture=BoundedProcessCapture(state,output_limit=4096,parse_markers=False)
            output,error,peak=drain_readonly(state,capture,45)
            self.assertEqual(state.returncode,0);self.assertEqual(error,'')
            result=json.loads(output)
            self.assertEqual(result['state'],'one_actual_host_bound_wrapper_denial_contract_pass_not_native')
            self.assertTrue(result['fixed_denial_not_external_input'])
            self.assertFalse(result['actual_Hangul_or_COM'] or result['native_directory_created'])
            self.assertGreaterEqual(peak,2)
            reader.finish()
            self.assertEqual(reader.final_fresh_hashes,len(reader.snapshots))
            state.profile['qualification_source_reads']=dict(fresh=len(reader.snapshots),final=reader.final_fresh_hashes)
            state.profile['actual_target_result']=result;state.profile['maximum_active_owned_processes']=peak
        finally:
            if capture is not None:capture.close()
            state.close()
        self.actual.append(copy.deepcopy(state.profile))


    def test_09_nested_cpu_uses_verified_parent_not_squared_machine_quota(self):
        windows=NS(mask=1,cpu_rate=625)
        parent=dict(job_present=True,query_succeeded=True,flags=0x2238,affinity=1,priority=0x4000,
            rate_flags=5,rate=625)
        budget=host.cpu_budget(windows,parent)
        self.assertTrue(budget['verified_parent_budget'])
        self.assertEqual(budget['configured_rate'],10000)
        self.assertEqual(budget['machine_percent_upper_bound'],6.25)
        stricter=host.cpu_budget(windows,dict(parent,rate=300))
        self.assertEqual(stricter['machine_percent_upper_bound'],3)

    def test_10_unknown_or_weaker_parent_keeps_original_child_quota(self):
        windows=NS(mask=1,cpu_rate=625)
        parent=dict(job_present=True,query_succeeded=True,flags=0x2238,affinity=1,priority=0x4000,
            rate_flags=5,rate=625)
        for change in (dict(job_present=False),dict(query_succeeded=False),dict(rate=10000),
                dict(rate_flags=1),dict(rate=True),dict(flags=0x2238|0x800),dict(affinity=3),dict(priority=0x20)):
            budget=host.cpu_budget(windows,dict(parent,**change))
            self.assertFalse(budget['verified_parent_budget'])
            self.assertEqual(budget['configured_rate'],625)


if __name__=='__main__':
    cpu_only=sys.argv[1:]==['--cpu-change-only']
    if sys.argv[1:] and not cpu_only:raise SystemExit(2)
    suite=unittest.TestSuite([OwnedHostContracts(name) for name in
        unittest.defaultTestLoader.getTestCaseNames(OwnedHostContracts) if not cpu_only or
        int(name.split('_')[1])>=6])
    result=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(suite)
    failures=[dict(test=t.id(),last_line=trace.splitlines()[-1][:160]) for t,trace in result.errors+result.failures]
    print(json.dumps(dict(state=('five_cpu_parent_host_contracts_pass_not_native' if cpu_only else 'ten_owned_host_partition_contracts_pass_not_native') if result.wasSuccessful()
        else 'owned_host_partition_contract_failed',passed=result.testsRun-len(failures),failed=len(failures),declared=result.testsRun,
        failures=failures,actual_host_profiles=OwnedHostContracts.actual,prior_five_not_reexecuted=cpu_only,actual_Hangul_or_COM=False,
        native_execution_authorized=False,coordinator_in_host_job=False,
        complete_native_guard_integration_qualified=False,p09_complete=False)))
    raise SystemExit(0 if result.wasSuccessful() else 2)
