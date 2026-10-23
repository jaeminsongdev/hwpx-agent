"""Exact original profile and CPU State with synthetic sampler; no OS IO."""
from pathlib import Path
import sys
from types import SimpleNamespace as NS
import unittest

import batch_product_runtime as driver
import preparation_attributed_cpu_v1 as policy
import preparation_checkpoint_owner as module

RAW = None


def fixture(*, wrapped=False, guarded=True):
    f = NS(identity=[(1, 2)], original_calls=0, native_calls=0)
    relay = NS(phase='PREPARATION')
    auditor = driver.ProcessPolicy(Path('D:/synthetic'), product=False)
    class Guard:
        def __init__(self):
            self.samples = []
            self.state = policy.State(16, 'dispatch_construction')
            self.sampling = False
        def check(self, *args, **kwargs):
            f.original_calls += 1
            if relay.phase != 'PREPARATION':
                f.native_calls += 1
                return 'original_native'
            if f.original_calls > 1000:
                raise ValueError('TEST_BOUNDED_REENTRY')
            index = len(self.samples) + 1
            row = dict(system_cpu_percent=20, parent_cpu_machine_percent=1)
            self.samples.append(row)
            if not self.sampling:
                self.sampling = True
                try:
                    auditor('ctypes.addressof', ())
                finally:
                    self.sampling = False
            self.state.observe(index, float(index), row)
    guard = Guard()
    bridge = module.Checkpoint(relay, guard.check, RAW, identity=lambda: f.identity[0])
    if guarded:
        checkpoint = bridge.checkpoint
        if wrapped:
            # Same actual Closing call shape; no fake profile identity accepted.
            class Closing:
                def __init__(self):
                    self.original_checkpoint = bridge.checkpoint
                    self.checkpoint = self.check
                def check(self):
                    return self.original_checkpoint()
            checkpoint = Closing().checkpoint
    else:
        checkpoint = guard.check
    reader = NS(checkpoint=checkpoint)
    bridge.bind_reader(reader)
    audit_state = dict(active=True, checking=False)
    profile = module.original_profile_factory(RAW)(audit_state, reader)
    f.__dict__.update(relay=relay, guard=guard, bridge=bridge, reader=reader,
        profile=profile, audit_state=audit_state)
    return f


def profiled(f):
    try:
        sys.setprofile(f.profile)
        f.reader.checkpoint()
    finally:
        sys.setprofile(None)


class Tests(unittest.TestCase):
    def test_original_uncoalesced_sampler_reproduces_fresh_sequence_error(self):
        f = fixture(guarded=False)
        with self.assertRaisesRegex(ValueError, 'FRESH_SAMPLE_SEQUENCE'):
            profiled(f)
        self.assertGreater(len(f.guard.samples), f.guard.state.decisions + 1)

    def test_original_profile_requests_coalesced_without_sample_rewrite(self):
        f = fixture()
        profiled(f)
        self.assertFalse(f.bridge.failed)
        self.assertGreater(f.bridge.coalesced, 0)
        self.assertEqual(f.guard.state.decisions, len(f.guard.samples))
        self.assertEqual(f.guard.state.index, len(f.guard.samples))
        self.assertFalse(f.bridge.evidence()['original_profile_callbacks_skipped'])

    def test_actual_reader_closing_call_shape_supported(self):
        f = fixture(wrapped=True)
        profiled(f)
        self.assertGreater(f.bridge.coalesced, 0)
        self.assertEqual(f.guard.state.decisions, len(f.guard.samples))

    def test_nonprofile_recursive_request_is_rejected_not_silently_skipped(self):
        f = fixture()
        def recursive():
            f.bridge.checkpoint()
        f.bridge.original = recursive
        with self.assertRaisesRegex(ValueError, 'ONLY_EXACT_ORIGINAL_PROFILER_REENTRY'):
            f.bridge.checkpoint()
        self.assertTrue(f.bridge.failed)

    def test_foreign_reader_or_profile_body_not_admitted(self):
        for changed in ('reader', 'body'):
            f = fixture()
            if changed == 'reader':
                f.profile = module.original_profile_factory(RAW)(f.audit_state, NS(checkpoint=f.reader.checkpoint))
            else:
                code = f.profile.__code__
                f.profile.__code__ = code.replace(co_consts=tuple('other_scope/' if v == 'tools/p09/' else v for v in code.co_consts))
            f.bridge.inflight = True
            with self.assertRaises(ValueError):
                profiled(f)
            self.assertTrue(f.bridge.failed)

    def test_guard_failure_preserved_and_permanently_latched(self):
        f = fixture()
        error = ValueError('STOP_PREPARATION_SYSTEM_PRESSURE90')
        def fail():
            raise error
        f.bridge.original = fail
        with self.assertRaises(ValueError) as caught:
            f.bridge.checkpoint()
        self.assertIs(caught.exception, error)
        f.bridge.original = lambda: None
        with self.assertRaises(ValueError):
            f.bridge.checkpoint()

    def test_native_delegates_even_during_preparation_inflight_flag(self):
        f = fixture()
        f.relay.phase = 'NATIVE'
        f.bridge.inflight = True
        self.assertEqual(f.bridge.checkpoint(), 'original_native')
        self.assertEqual(f.native_calls, 1)
        self.assertEqual(f.bridge.coalesced, 0)

    def test_original_native_recursion_or_pressure_failure_identity_unchanged(self):
        f = fixture()
        error = ValueError('BATCH_NATIVE_CHECKPOINT_NO_RECURSIVE_CHECKPOINT_CYCLE')
        def fail():
            raise error
        f.bridge.original = fail
        f.relay.phase = 'NATIVE'
        with self.assertRaises(ValueError) as caught:
            f.bridge.checkpoint()
        self.assertIs(caught.exception, error)
        self.assertEqual(f.bridge.coalesced, 0)

    def test_foreign_owner_or_changed_original_source_fails_closed(self):
        f = fixture()
        f.identity[0] = (1, 3)
        with self.assertRaises(ValueError):
            f.bridge.checkpoint()
        with self.assertRaisesRegex(ValueError, 'EXACT_WHOLE_ORIGINAL_SOURCE'):
            module.original_profile_factory(RAW + b' ')


if __name__ == '__main__':
    unittest.main()
