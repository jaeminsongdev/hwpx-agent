"""New native-host limit contracts; no Hancom activation or document output."""
import ast
import copy
import ctypes
from ctypes import wintypes as w
import io
import json
import os
from pathlib import Path
import sys
from types import SimpleNamespace as NS
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools/p09'))
import crossref_native_host_limits as native


def owner():
    return dict(process_id=os.getpid(), session_id=1, created_at_utc='2026-10-17T00:00:00.1234567Z',
        executable_sha256=native.EXECUTABLE_SHA, window_handle_binds_exact_process=True)


class NativeHostLimitsContracts(unittest.TestCase):
    actual_profiles = []

    def test_01_lossless_filetime_ticks(self):
        first = native.creation_ticks('2026-10-17T00:00:00.0000000Z')
        self.assertEqual(native.creation_ticks('2026-10-17T00:00:00.0000001Z')-first, 1)
        self.assertEqual(native.creation_ticks('2026-10-17T00:00:00.9999999Z')-first, 9999999)
        for bad in (None, '', '2026-10-17T00:00:00Z', '2026-10-17T00:00:00.000001Z',
                '2026-10-17T00:00:00.0000000+00:00', '2026-02-31T00:00:00.0000000Z'):
            with self.assertRaises(ValueError):
                native.creation_ticks(bad)

    def test_02_exact_owner_schema_types_and_signed_handle(self):
        good = owner()
        for handle in (1, -1, 2**31-1, -2**31):
            self.assertGreater(native.validate_identity(good, handle), 0)
        for handle in (0, True, 2**31, -2**31-1, '1'):
            with self.assertRaises(ValueError):
                native.validate_identity(good, handle)
        changes = [dict(process_id=True), dict(session_id=True), dict(process_id=0),
            dict(window_handle_binds_exact_process=1), dict(executable_sha256='0'*64), dict(extra=True)]
        for change in changes:
            with self.assertRaises(ValueError):
                native.validate_identity(dict(good, **change), 1)
        with self.assertRaises(ValueError):
            native.validate_identity({k:v for k,v in good.items() if k!='created_at_utc'}, 1)

    def test_03_partition_keeps_combined_eight_percent_and_shared_cpu(self):
        total = 32*1024**3
        windows = NS(processors=16, mask=1, cpu_rate=625, total_ram=total,
            memory_limit=(total*8//100)//4096*4096)
        plan = native.validate_plan(windows)
        self.assertLessEqual(plan['memory_limit'] + windows.memory_limit//8, windows.memory_limit)
        self.assertGreater(plan['memory_limit'], 0)
        self.assertEqual(plan['cpu_rate'], 625)
        self.assertEqual(plan['affinity'], windows.mask)
        self.assertEqual(plan['flags'] & (0x2000|0x1800|0x2|0x4), 0)
        for change in (dict(mask=3), dict(cpu_rate=10000), dict(memory_limit=total), dict(processors=True)):
            with self.assertRaises(ValueError):
                native.validate_plan(NS(**dict(vars(windows), **change)))

    def test_04_no_launcher_kill_timer_or_native_entry(self):
        tree = ast.parse((ROOT/native.SELF).read_text(encoding='utf-8'))
        calls = [n.func.attr if isinstance(n.func, ast.Attribute) else n.func.id
            for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, (ast.Name, ast.Attribute))]
        self.assertFalse(set(calls) & {'Popen','run','system','TerminateJobObject','TerminateProcess','kill','sleep'})
        self.assertFalse(any(isinstance(n, ast.If) and '__name__' in ast.unparse(n.test) for n in tree.body))

    def test_05_nonempty_close_never_drops_limits_or_kills(self):
        state = native.NativeOwnerJob.__new__(native.NativeOwnerJob)
        state.closed=False;state.job=123;state.profile=dict(cleanup_confirmed=False)
        closed=[];state.k=NS(CloseHandle=lambda h:closed.append(h))
        state.windows=NS(accounting=lambda h:dict(active_processes=1))
        with self.assertRaisesRegex(ValueError, 'OWNED_PROCESS_STILL_ALIVE_NO_FORCE_CLOSE'):
            state.close()
        self.assertEqual(closed, [])
        self.assertEqual(state.job, 123)
        self.assertFalse(state.closed)

    def test_06_admission_latches_before_bad_identity_without_os_calls(self):
        state = native.NativeOwnerJob.__new__(native.NativeOwnerJob)
        state.closed=False;state.admission_attempted=False;state.admission_failed=False
        with self.assertRaisesRegex(ValueError, 'IDENTITY_SCHEMA'):
            state.admit({}, 1)
        self.assertTrue(state.admission_attempted and state.admission_failed)
        with self.assertRaisesRegex(ValueError, 'NO_ADMISSION_RETRY'):
            state.admit(owner(), 1)

    def test_07_cleanup_does_not_call_stopped_checkpoint(self):
        state = native.NativeOwnerJob.__new__(native.NativeOwnerJob)
        state.closed=False;state.job=123;state.profile=dict(cleanup_confirmed=False)
        state.checkpoint=lambda:(_ for _ in ()).throw(ValueError('STOP_TEST'))
        closed=[];state.k=NS(CloseHandle=lambda h:closed.append(h) or True)
        state.windows=NS(accounting=lambda h:dict(active_processes=0))
        state.close();state.close()
        self.assertEqual(closed, [123])
        self.assertTrue(state.closed and state.profile['cleanup_confirmed'])

    def test_08_private_pressure_uses_unrounded_accounting(self):
        state = native.NativeOwnerJob.__new__(native.NativeOwnerJob)
        state.closed=False;state.job=123;state.profile={};state.checkpoint=lambda:None
        state.plan=dict(memory_limit=1048576)
        state.windows=NS(total_ram=100000000, accounting=lambda h:
            dict(peak_job_private_mib=0, peak_job_private_percent=1))
        with self.assertRaisesRegex(ValueError, 'STOP_PARTITIONED_PRIVATE_MEMORY'):
            state.observe()

    def test_09_actual_empty_job_readback_and_safe_close(self):
        windows = native.c.Windows()
        state = native.NativeOwnerJob(windows, lambda:None, lambda:None)
        try:
            readback = state.readback()
            self.assertTrue(readback['verified'])
            self.assertFalse(readback['kill_on_close'] or readback['time_limit_installed'])
            self.assertEqual(state.observe()['active_processes'], 0)
            self.assertFalse(state.profile['native_process_assigned'])
        finally:
            state.close()
        self.actual_profiles.append(copy.deepcopy(state.profile))

    def test_10_actual_python_process_rejected_before_assignment_or_pin_read(self):
        windows = native.c.Windows()
        opened=[]
        state = native.NativeOwnerJob(windows, lambda:None, lambda:opened.append(True))
        try:
            with self.assertRaisesRegex(ValueError, 'PROCESS_IMAGE'):
                state.admit(owner(), 1)
            self.assertTrue(state.admission_failed)
            self.assertFalse(state.profile['native_process_assigned'])
            self.assertEqual(opened, [])
            self.assertEqual(state.observe()['active_processes'], 0)
            with self.assertRaisesRegex(ValueError, 'NO_ADMISSION_RETRY'):
                state.admit(owner(), 1)
        finally:
            state.close()
        self.actual_profiles.append(copy.deepcopy(state.profile))


if __name__ == '__main__':
    stream = io.StringIO()
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(NativeHostLimitsContracts)
    result = unittest.TextTestRunner(stream=stream, verbosity=0).run(suite)
    failures = [dict(test=test.id(), last_line=trace.splitlines()[-1][:160])
        for test,trace in result.errors+result.failures]
    print(json.dumps(dict(state='ten_native_host_limit_contracts_pass_not_native' if result.wasSuccessful()
        else 'native_host_limit_contract_failed', passed=result.testsRun-len(failures), failed=len(failures),
        declared=result.testsRun, failures=failures, actual_empty_job_profiles=NativeHostLimitsContracts.actual_profiles,
        actual_Hangul_or_COM=False, native_execution_authorized=False, host_one_percent_job_installed=False,
        complete_native_guard_integration_qualified=False, p09_complete=False)))
    raise SystemExit(0 if result.wasSuccessful() else 2)
