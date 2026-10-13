import ctypes
import math
from pathlib import Path
import sys
import threading
from types import SimpleNamespace as NS
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import metadata_pressure_failfast as m
import system_commit_diagnostic as d


class MetadataContracts(unittest.TestCase):
    def make(self, value=40):
        events = []
        owner = NS(lock=threading.Lock(), samples=[dict(system_cpu_percent=value)],
                   checkpoint_io=lambda: events.append('hard'))
        reader = NS(checkpoint=lambda: events.append('original'))
        guard = m.Checkpoint(reader, owner)
        return events, owner, reader, guard

    def test_cool_path_retains_both_callbacks(self):
        events, _, reader, guard = self.make(74.99)
        reader.checkpoint()
        guard.restore()
        self.assertEqual(events, ['hard', 'original'])
        self.assertTrue(guard.restored)

    def test_warning_has_no_original_cooling_or_resume(self):
        events, owner, reader, guard = self.make(75)
        with self.assertRaisesRegex(ValueError, 'STOP_METADATA_WARNING'):
            reader.checkpoint()
        owner.samples[:] = [dict(system_cpu_percent=1)]
        with self.assertRaisesRegex(ValueError, 'STOP_LATCHED'):
            reader.checkpoint()
        self.assertEqual(events, ['hard'])
        self.assertEqual(guard.warning_stops, 1)
        guard.restore()

    def test_cleanup_is_unconditional_and_idempotent(self):
        _, owner, reader, guard = self.make(100)
        with self.assertRaises(ValueError):
            reader.checkpoint()
        owner.checkpoint_io = lambda: self.fail('cleanup must not guard')
        guard.restore()
        guard.restore()
        self.assertFalse(guard.active)
        self.assertTrue(guard.restored)

    def test_original_hard_error_has_precedence(self):
        events, _, reader, guard = self.make(100)
        def hard():
            raise ValueError('STOP_SYSTEM_COMMIT_PRESSURE')
        guard.hard = hard
        with self.assertRaisesRegex(ValueError, '^STOP_SYSTEM_COMMIT_PRESSURE$'):
            reader.checkpoint()
        self.assertFalse(guard.latched)
        self.assertEqual(events, [])
        guard.restore()

    def test_invalid_or_missing_sample_fails_closed(self):
        for value in (True, -1, 101, math.nan, '40', None):
            _, _, reader, guard = self.make(value)
            with self.subTest(value=value), self.assertRaises(ValueError):
                reader.checkpoint()
            guard.restore()
        _, owner, reader, guard = self.make()
        owner.samples.clear()
        with self.assertRaisesRegex(ValueError, 'SAMPLE_MISSING'):
            reader.checkpoint()
        guard.restore()

    def test_callback_drift_cannot_be_restored_or_read(self):
        _, _, reader, guard = self.make()
        reader.checkpoint = lambda: None
        with self.assertRaises(ValueError):
            guard.restore()
        with self.assertRaises(ValueError):
            guard()

    def test_checkpoint_has_no_io_sleep_query_or_runner_dependency(self):
        import ast
        tree = ast.parse(Path(m.__file__).read_text(encoding='utf-8'))
        imports = [alias.name for n in ast.walk(tree) if isinstance(n, ast.Import) for alias in n.names]
        self.assertEqual(imports, ['math'])
        self.assertFalse(any(isinstance(n, ast.ImportFrom) for n in ast.walk(tree)))


class CommitContracts(unittest.TestCase):
    def run_query(self, *, ok=True, limit=100, used=30, available=50, elapsed=.001):
        calls = []
        def query(pointer, size):
            calls.append(size)
            info = ctypes.cast(pointer, ctypes.POINTER(d.PerformanceInformation)).contents
            info.CommitLimit = limit
            info.CommitTotal = used
            info.PhysicalTotal = 100
            info.PhysicalAvailable = available
            info.PageSize = 4096
            return ok
        times = iter((0., elapsed))
        result = d.once(NS(K32GetPerformanceInfo=query), clock=lambda: next(times))
        self.assertEqual(calls, [ctypes.sizeof(d.PerformanceInformation)])
        return result

    def test_global_commit_uses_pages_not_process_limit(self):
        row = self.run_query()
        self.assertTrue(row['available'])
        self.assertEqual(row['system_commit_used_percent'], 30)
        self.assertEqual(row['system_commit_limit_bytes'], 409600)
        self.assertFalse(row['replaces_original_resource_decisions'])

    def test_late_query_is_unavailable_not_zero(self):
        row = self.run_query(elapsed=.051)
        self.assertFalse(row['available'])
        self.assertEqual(row['reason'], 'DIAGNOSTIC_COST_BUDGET_EXCEEDED')
        self.assertNotIn('system_commit_used_percent', row)

    def test_failed_query_is_unavailable_not_zero(self):
        row = self.run_query(ok=False)
        self.assertFalse(row['available'])
        self.assertNotIn('system_commit_used_percent', row)

    def test_invalid_values_are_rejected(self):
        for args in (dict(limit=0), dict(used=101), dict(available=101)):
            with self.subTest(args=args):
                self.assertFalse(self.run_query(**args)['available'])

    def test_native_layout_size(self):
        self.assertEqual(ctypes.sizeof(d.PerformanceInformation),
                         104 if ctypes.sizeof(ctypes.c_void_p) == 8 else 56)


if __name__ == '__main__':
    unittest.main()
