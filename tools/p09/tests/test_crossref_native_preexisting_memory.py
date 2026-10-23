"""Only the pre-assignment memory delta and one affected prior pressure test."""
import io
import json
from pathlib import Path
import sys
from types import SimpleNamespace as NS
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools/p09'))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import crossref_native_host_limits as native
from test_crossref_native_host_limits import NativeHostLimitsContracts


class PreexistingMemoryContracts(unittest.TestCase):
    def test_11_prior_allocations_and_new_growth_both_count(self):
        self.assertEqual(native.combined_private_budget(8000, 3000, 3, 100000), 6000)
        for before,peak in ((7000,0), (6000,1), (0,7), (6999,1)):
            with self.assertRaisesRegex(ValueError, 'STOP_PARTITIONED_PRIVATE_MEMORY'):
                native.combined_private_budget(8000, before, peak, 100000)
        for before,peak in ((True,0), (-1,0), (0,True), (0,float('nan')), (0,float('inf'))):
            with self.assertRaises(ValueError):
                native.combined_private_budget(8000, before, peak, 100000)

    def test_12_oversized_owned_handle_denied_before_assign_and_not_retried(self):
        # Pure backend model: do not replace live Windows/COM functions or admit a real PID.
        state = native.NativeOwnerJob.__new__(native.NativeOwnerJob)
        state.closed=False;state.admission_attempted=False;state.admission_failed=False;state.job=123
        state.profile=dict(native_process_assigned=False, pre_assignment_private_bytes=0)
        state.plan=dict(memory_limit=8000);closed=[];assigned=[]
        state.k=NS(OpenProcess=lambda *a:42,CloseHandle=lambda h:closed.append(h) or True,
            AssignProcessToJobObject=lambda *a:assigned.append(True))
        state.windows=NS(total_ram=100000,accounting=lambda h:dict(active_processes=0))
        state.checkpoint=lambda:None;state.readback=lambda:None
        state._observe_identity=lambda *a:None
        state._private_bytes=lambda h:7000
        state.fresh_executable_pin=lambda:dict(sha256=native.EXECUTABLE_SHA, bytes=native.EXECUTABLE_BYTES)
        identity=dict(process_id=10,session_id=1,created_at_utc='2026-10-17T00:00:00.0000000Z',
            executable_sha256=native.EXECUTABLE_SHA,window_handle_binds_exact_process=True)
        with self.assertRaisesRegex(ValueError, 'STOP_PARTITIONED_PRIVATE_MEMORY'):
            state.admit(identity, 1)
        self.assertEqual(assigned, [])
        self.assertEqual(closed, [42])
        self.assertTrue(state.admission_failed)
        self.assertFalse(state.profile['native_process_assigned'])
        with self.assertRaisesRegex(ValueError, 'NO_ADMISSION_RETRY'):
            state.admit(identity, 1)


if __name__ == '__main__':
    suite=unittest.TestSuite([NativeHostLimitsContracts('test_08_private_pressure_uses_unrounded_accounting')])
    suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(PreexistingMemoryContracts))
    result=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(suite)
    failures=[dict(test=t.id(),last_line=trace.splitlines()[-1][:160]) for t,trace in result.errors+result.failures]
    print(json.dumps(dict(state='three_memory_delta_contracts_pass_not_native' if result.wasSuccessful()
        else 'native_preexisting_memory_contract_failed',passed=result.testsRun-len(failures),failed=len(failures),
        declared=result.testsRun,prior_tests_reused=9,prior_pressure_test_reexecuted=1,new_memory_contracts=2,
        failures=failures,actual_Hangul_or_COM=False,native_execution_authorized=False,p09_complete=False)))
    raise SystemExit(0 if result.wasSuccessful() else 2)
