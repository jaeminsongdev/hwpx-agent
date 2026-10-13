import copy
import io
import json
import threading
import unittest
from types import SimpleNamespace
import resume_compact_pressure_runtime as d
FIXTURES = None


class CompactBridgeTests(unittest.TestCase):
    def setUp(self):
        if FIXTURES is None:
            raise RuntimeError('FRESH_COMPACT_QUEUE_FIXTURES_REQUIRED')
        self.legacy, self.base, self.names = copy.deepcopy(FIXTURES)
    def test_next_is_unaccepted_regular(self):
        _, name = d.g.old.select(self.base, self.names)
        self.assertNotIn(name, self.base['runtime_qualified_test_names'])
    def test_advance_does_not_change_previous_plan(self):
        before = copy.deepcopy(self.base)
        index, _ = d.g.old.select(self.base, self.names)
        plan = d.g.advance(self.legacy, self.base, self.names, index)
        self.assertEqual(plan['runtime_source_qualified_individual_cases'], before['runtime_source_qualified_individual_cases'] + 1)
        self.assertEqual(before, self.base)
    def test_original_full_scope_is_extended_not_replaced(self):
        self.assertEqual(len(d.NEW), 5)
        self.assertEqual(len(d.EXTRAS), 31)
        self.assertTrue(set(d.h.EXTRAS) < set(d.EXTRAS))
    def test_original_parent_keywords_and_guard_are_connected(self):
        calls = []
        frame = SimpleNamespace(check=lambda: calls.append(True))
        completed = []
        stream = io.StringIO()
        doc = {'text': '한글', 'samples': [{'cpu': 98.0}], 'cleanup': True}
        d.parent_writer(frame, completed)(doc, stream, ensure_ascii=False, indent=2)
        self.assertEqual(json.loads(stream.getvalue()), doc)
        self.assertTrue(stream.getvalue().isascii())
        self.assertEqual(len(completed), 1)
        self.assertGreaterEqual(len(calls), 4)
        d.stats_contract(completed[0], {'bytes': len(stream.getvalue())})
    def test_parent_original_stop_cannot_be_swallowed(self):
        def stop():
            raise ValueError('STOP_SUSTAINED_SYSTEM_CPU')
        with self.assertRaisesRegex(ValueError, 'STOP_SUSTAINED_SYSTEM_CPU'):
            d.parent_writer(SimpleNamespace(check=stop), [])({}, io.StringIO(), ensure_ascii=False, indent=2)
    def test_parent_keyword_drift_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'EXACT_ORIGINAL_PARENT_DUMP_OPTIONS'):
            d.parent_writer(SimpleNamespace(check=lambda: None), [])({}, io.StringIO(), indent=2)
    def test_terminal_write_does_not_restart_resource_owner(self):
        done = threading.Event()
        owner = SimpleNamespace(done=done)
        with self.assertRaises(ValueError):
            d.terminal_checkpoint({'state': d.PASS}, owner)
        done.set()
        d.terminal_checkpoint({'state': d.PASS}, owner)
        d.terminal_checkpoint({'state': 'FAILED_NOT_ACCEPTED', 'error_code': 'STOP_CPU'}, owner)
    def test_failed_actual_or_admission_blocks_retry(self):
        for flags in ({'product_worker_invocation_requested': False}, {'frame_acquisition_complete': True}):
            with self.subTest(flags=flags), self.assertRaisesRegex(ValueError, 'INSPECT_ANY_FAILED'):
                d.closed_attempt(dict(state='FAILED_NOT_ACCEPTED', resource_stop_reason='STOP_SUSTAINED_SYSTEM_CPU', **flags))
    def test_failed_cleanup_is_not_accepted(self):
        with self.assertRaisesRegex(ValueError, 'INSPECT_ANY_FAILED'):
            d.closed_attempt(dict(state=d.PASS, error_code=None, resource_stop_reason=None,
                resource_watcher_cleanup_confirmed=False))
    def test_policy_preserves_fields_and_never_claims_CPU_improvement(self):
        row = d.policy()
        self.assertEqual(row['semantic_fields_removed'], 0)
        self.assertTrue(row['parent_original_frame_guard_connected'])
        self.assertFalse(row['new_sampler_started'])
        self.assertFalse(row['original_receipts_rewritten'])
        self.assertFalse(row['CPU_or_PC_freeze_improvement_claimed'])
