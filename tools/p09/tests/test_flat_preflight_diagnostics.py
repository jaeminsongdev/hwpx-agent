"""Preflight failure-report contracts; synthetic guards, no product execution."""
import ast
import contextlib
import copy
import io
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import flat_current_queue_acceptance as m

r = m.r
a = m.a
CHECKPOINT = lambda: None
SCRIPT = 'tools/p09/preflight_flat_current_queue.ps1'


class PreflightDiagnostics(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        q = a.AcceptanceReader(r.c.ROOT, CHECKPOINT)
        source = q.text(SCRIPT)
        cls.payload = source.split("@'\n", 1)[1].split("\n'@", 1)[0]
        cls.code = compile(cls.payload, SCRIPT + ':embedded-python', 'exec')
        cls.step = r.load_config(118)
        q.finish()

    @staticmethod
    def sample(cpu=10., ram=50., commit=35.):
        return dict(time_utc='SYNTHETIC_CONTRACT_ONLY_NOT_MEASUREMENT',
                    system_cpu_percent=cpu, available_ram_percent=ram,
                    commit_used_percent=commit, parent_cpu_machine_percent=None,
                    parent_private_mib=0., parent_private_percent=0.)

    def simulate(self, samples, close_error=False, configuration_error=False):
        CHECKPOINT()
        class FakeGuard:
            def __init__(self):
                self.samples = copy.deepcopy(samples)
                self.cleanup = False
                self.close_called = False
            def acquire(self):
                raise ValueError('CURRENT_EPOCH_ACCEPT_ORIGINAL_RESOURCE_STOP')
            def close(self):
                self.close_called = True
                if close_error:
                    raise ValueError('SYNTHETIC_CLEANUP_ERROR')
                self.cleanup = True
        buffer = io.StringIO()
        cfg = patch.object(r, 'configure', side_effect=ValueError('FLAT_QUEUE_CONFIG_CURSOR')) if configuration_error else patch.object(r, 'configure', return_value=self.step)
        with patch.object(a, 'Guard', FakeGuard), cfg, patch.object(sys, 'argv', ['-c', '118']), patch.object(r, 'binding_attempt') as body, contextlib.redirect_stdout(buffer):
            with self.assertRaises(SystemExit) as stopped:
                exec(self.code, {'__name__': '__preflight_contract__'})
        self.assertEqual(stopped.exception.code, 2)
        body.assert_not_called()
        row = json.loads(buffer.getvalue())
        self.assertEqual(row['state'], 'STOPPED_FLAT_PREFLIGHT_NOT_NATIVE_PRODUCT_OR_ACCEPTANCE')
        self.assertFalse(row['product_worker_or_Native_frame_executed'])
        self.assertEqual(row['queue_delta'], 0)
        self.assertFalse(row['PC_freeze_resolved'])
        self.assertFalse(row['second_sampler_or_external_profiler'])
        CHECKPOINT()
        return row

    def test_original_guard_finish_force_wait_and_no_real_body_invocation_structure(self):
        ast.parse(self.payload)
        for statement in ('g = a.Guard()', 'g.acquire()', 'q.finish()', 'time.sleep(.5)', 'g.check(force=True)', 'g.close()', 'r.binding_attempt(q, 1)'):
            self.assertIn(statement, self.payload)
        self.assertNotIn('r.run_owned(', self.payload)
        self.assertNotIn('engine.run_owned(', self.payload)
        self.assertNotIn('run(root_pin)', self.payload)
        self.assertLess(len(self.payload), 32768)

    def test_CPU_stop_reason_and_unknown_parent_CPU_not_fabricated(self):
        row = self.simulate([self.sample(cpu=99.) for _ in range(4)])
        self.assertEqual(row['original_resource_stop_reasons'], ['STOP_SUSTAINED_SYSTEM_CPU'])
        self.assertEqual(row['original_resource_samples'], 4)
        self.assertIsNone(row['parent_CPU_max_machine_percent'])
        self.assertTrue(row['cleanup_confirmed'])
        self.assertEqual(row['stage'], 'admission')

    def test_RAM_stop_and_tail_bounded_to_six_existing_samples(self):
        row = self.simulate([self.sample(ram=1.) for _ in range(8)])
        self.assertEqual(row['original_resource_stop_reasons'], ['STOP_LOW_AVAILABLE_RAM'])
        self.assertEqual(row['original_resource_samples'], 8)
        self.assertEqual(len(row['original_sample_tail']), 6)
        self.assertEqual(row['original_sample_tail_limit'], 6)
        self.assertTrue(row['cleanup_confirmed'])

    def test_commit_stop_remains_distinct(self):
        row = self.simulate([self.sample(commit=96.)])
        self.assertEqual(row['original_resource_stop_reasons'], ['STOP_SYSTEM_COMMIT_PRESSURE'])
        self.assertEqual(row['error_code'], 'CURRENT_EPOCH_ACCEPT_ORIGINAL_RESOURCE_STOP')

    def test_cleanup_failure_never_promoted_to_PASS(self):
        row = self.simulate([self.sample(ram=1.)], close_error=True)
        self.assertEqual(row['error_code'], 'ORIGINAL_GUARD_CLEANUP_FAILED')
        self.assertFalse(row['cleanup_confirmed'])

    def test_configuration_failure_has_no_fabricated_samples_or_cleanup(self):
        row = self.simulate([], configuration_error=True)
        self.assertEqual(row['stage'], 'configuration')
        self.assertEqual(row['error_code'], 'FLAT_QUEUE_CONFIG_CURSOR')
        self.assertEqual(row['original_resource_samples'], 0)
        self.assertIsNone(row['system_CPU_max_percent'])
        self.assertIsNone(row['available_RAM_min_percent'])
        self.assertFalse(row['cleanup_confirmed'])


if __name__ == '__main__':
    guard = a.Guard()
    result = None
    try:
        guard.acquire()
        CHECKPOINT = guard.check
        result = unittest.TextTestRunner(verbosity=1).run(unittest.defaultTestLoader.loadTestsFromTestCase(PreflightDiagnostics))
    finally:
        guard.close()
    print(json.dumps(dict(state='PREFLIGHT_DIAGNOSTIC_CONTRACTS_ONLY_NOT_PRODUCT',
        contract_count=result.testsRun if result else 0, passed=bool(result and result.wasSuccessful()),
        synthetic_guard_samples_are_not_measurements=True, product_or_Native_executed=False,
        queue_delta=0, cleanup_confirmed=guard.cleanup)))
    raise SystemExit(0 if result and result.wasSuccessful() and guard.cleanup else 2)
