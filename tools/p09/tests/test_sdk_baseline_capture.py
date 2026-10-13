"""In-memory trace/component controls, NEVER create synthetic native evidence."""
import copy
import json
import unittest
from unittest.mock import patch
from tools.p09 import sdk_baseline_capture as c
from tools.p09 import sdk_baseline_native_queue as queue


def complete(row, pins, bundle_sha):
    trace = {name: None for name in c.TRACE_KEYS}
    trace.update(schema_version='hwpx-agent.p09-58-sdk-baseline-target-trace/v1', case_id=row['case_id'],
        capture_index=row['capture_index'], state=c.COMPLETE, started_at_utc='2026-10-03T00:00:00.0000000Z',
        completed_at_utc='2026-10-03T00:00:05.0000000Z', target=copy.deepcopy(c.q.field.TARGET),
        source_sha256=row['source_sha256'], source_bytes=row['source_bytes'], bundle_sha256=bundle_sha,
        harness_sha256=pins[c.HARNESS], owned_library_sha256=pins[c.LIBRARY],
        security_module_sha256='9ac5b97c47ac8aed1e8bca27a3eef39411361d8f68c262509f0c40a8f9d21bb6',
        source_identity_preserved=True, remaining_hwp_process_count=0)
    for name in c.FALSE_FIELDS: trace[name] = False
    trace['sessions'] = [{'label': label, 'version': '11.0.0.9136', 'register_module_return': False,
        'process': {'process_id': 200 + i, 'session_id': 1, 'created_at_utc': f'2026-10-03T00:00:0{i}.0000000Z',
            'executable_sha256': c.q.field.TARGET['executable_sha256'], 'window_handle_binds_exact_process': True},
        'close_without_dirty_prompt_returned': True, 'quit_invoked': True, 'remaining_owned_process_count': 0,
        'cleanup_error': None} for i, label in enumerate(('save', 'reopen'))]
    sdk = c.r.bounded(c.ROOT / row['source_file'], row['source_sha256'], 4194304)
    outputs = {'saved.hwpx': sdk, 'saved.pdf': b'%PDF-pure-component-not-native',
               'reopened.hwpx': sdk, 'reopened.pdf': b'%PDF-pure-component-not-native'}
    trace['artifacts'] = {name: {'sha256': c.sha(raw), 'bytes': len(raw)} for name, raw in outputs.items()}
    return trace, outputs


class Baselines(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = c.inputs()
        cls.pins = {name: c.sha(c.r.bounded(c.ROOT / name)) for name in (c.HARNESS, c.LIBRARY)}
        cls.bundle = c.inspect_bundle(cls.rows)['sha256']

    def bind(self, trace, code=0):
        return c.bind_trace(trace, self.rows[0], code, self.pins, self.bundle)

    def test_complete17_exact_sdk_inputs_and_field_target_not_original(self):
        self.assertEqual(tuple(row['case_id'] for row in self.rows), c.q.EXPECTED_IDS)
        self.assertEqual(len({row['source_file'] for row in self.rows}), 17)
        self.assertEqual(len({row['run_directory'] for row in self.rows}), 17)
        self.assertTrue(all(r['source_sha256'] == r['automation_input_sha256'] for r in self.rows[:15]))
        self.assertTrue(all(r['source_sha256'] != r['automation_input_sha256'] for r in self.rows[15:]))

    def test_bundle_exact_bytes_and_non_oracle_scope(self):
        value = json.loads(c.r.bounded(c.ROOT / c.BUNDLE))
        self.assertEqual(c.canonical(value), c.canonical(c.bundle(self.rows)))
        self.assertFalse(value['human_authored_direct_oracle'])
        self.assertFalse(value['p09_complete'])

    def test_command_fixed_scope_rejects_alias_and_bool_index(self):
        command = c.command(self.rows[0], self.pins, self.bundle)
        self.assertEqual(command[-1], '-PreflightOnly')
        for key, value in [('capture_index', True), ('run_directory', 'foreign'), ('source_sha256', '0' * 64)]:
            row = {**self.rows[0], key: value}
            self.assertRaises(ValueError, c.command, row, self.pins, self.bundle)

    def test_preflight_rejects_subset_before_child_activation(self):
        with patch.object(c.subprocess, 'run') as child:
            self.assertRaises(ValueError, c.actual_preflights, self.rows[:2], self.pins, self.bundle)
            child.assert_not_called()

    def test_all17_synthetic_complete_bind_only_non_green(self):
        for row in self.rows:
            trace, _ = complete(row, self.pins, self.bundle)
            value = c.bind_trace(trace, row, 0, self.pins, self.bundle)
            self.assertEqual(value['lifecycle'], 'pass')
            self.assertFalse(value['human_authored_direct_oracle'])
            self.assertFalse(value['native_package_render_differential_or_product_qualified'])

    def test_foreign_hashes_target_unknown_values_rejected(self):
        original, _ = complete(self.rows[0], self.pins, self.bundle)
        for key, value in [('source_sha256', '0'*64), ('bundle_sha256', '0'*64), ('owned_library_sha256', '0'*64),
                           ('capture_index', True), ('source_bytes', False), ('unexpected_raw_values', 'forbidden')]:
            trace = copy.deepcopy(original); trace[key] = value; self.assertRaises(ValueError, self.bind, trace)
        trace = copy.deepcopy(original); trace['target']['locale'] = 'unattested'; self.assertRaises(ValueError, self.bind, trace)

    def test_false_claims_require_actual_false(self):
        original, _ = complete(self.rows[0], self.pins, self.bundle)
        for name in c.FALSE_FIELDS:
            for value in (True, 0):
                trace = copy.deepcopy(original); trace[name] = value; self.assertRaises(ValueError, self.bind, trace)

    def test_actual_child_exit_no_boolean_or_cleanup_promotion(self):
        trace, _ = complete(self.rows[0], self.pins, self.bundle)
        for code in (False, True, 2, 1): self.assertRaises(ValueError, self.bind, trace, code)
        trace['sessions'][1]['cleanup_error'] = 'P58_OWNED_CLOSE_FAILED_NO_IMPLICIT_SAVE_OR_FORCE_KILL'
        trace['sessions'][1]['quit_invoked'] = False
        self.assertRaises(ValueError, self.bind, trace)
        value = self.bind(trace, 2)
        self.assertEqual((value['lifecycle'], value['failed_phase']), ('fail', 'owner_cleanup'))

    def test_owner_identity_birth_session_duplicates_rejected(self):
        original, _ = complete(self.rows[0], self.pins, self.bundle)
        for key, value in [('process_id', 200), ('process_id', True), ('session_id', 2),
                           ('created_at_utc', '2026-10-02T00:00:00.0000000Z'), ('window_handle_binds_exact_process', 1)]:
            trace = copy.deepcopy(original); trace['sessions'][1]['process'][key] = value
            self.assertRaises(ValueError, self.bind, trace)

    def test_time_order_and_source_loss_rejected(self):
        original, _ = complete(self.rows[0], self.pins, self.bundle)
        for key, value in [('completed_at_utc', '2026-10-02T00:00:00.0000000Z'), ('source_identity_preserved', False),
                           ('remaining_hwp_process_count', False)]:
            trace = copy.deepcopy(original); trace[key] = value; self.assertRaises(ValueError, self.bind, trace)

    def test_failed_first_open_has_no_invented_artifacts(self):
        trace, _ = complete(self.rows[0], self.pins, self.bundle)
        trace.update(state='effect_unknown', failed_phase='source_open', error_code='P58_OPEN_FAILED', artifacts={})
        trace['sessions'] = trace['sessions'][:1]
        value = self.bind(trace, 2)
        self.assertEqual(value['lifecycle'], 'fail')
        self.assertTrue(value['cleanup_safe_to_continue'])
        self.assertRaises(ValueError, self.bind, trace)

    def test_unresolved_owner_is_retained_failed(self):
        trace, _ = complete(self.rows[0], self.pins, self.bundle)
        trace.update(state='effect_unknown', failed_phase='first_session_create', error_code='P58_NATIVE_WINDOW_HANDLE_TYPE',
                     artifacts={}, remaining_hwp_process_count=1)
        trace['sessions'] = [{'label': 'save', 'version': None, 'register_module_return': None, 'process': None,
            'close_without_dirty_prompt_returned': False, 'quit_invoked': False, 'remaining_owned_process_count': -1,
            'cleanup_error': 'P58_OWNER_UNVERIFIED_NO_BLANKET_QUIT'}]
        value = self.bind(trace, 2)
        self.assertFalse(value['cleanup_safe_to_continue'])

    def test_artifact_prefix_and_reachability(self):
        original, _ = complete(self.rows[0], self.pins, self.bundle)
        for name in ('saved.hwpx', 'saved.pdf', 'reopened.hwpx'):
            trace = copy.deepcopy(original); trace['artifacts'].pop(name); self.assertRaises(ValueError, self.bind, trace)
        trace = copy.deepcopy(original); trace.update(state='effect_unknown', failed_phase='first_save', error_code='P58_NATIVE_SAVE_FAILED')
        self.assertRaises(ValueError, self.bind, trace)

    def test_actual_artifact_hash_size_and_missing_claim(self):
        trace, outputs = complete(self.rows[0], self.pins, self.bundle)
        for mode in ('changed', 'missing', 'extra'):
            altered = dict(outputs)
            if mode == 'changed': altered['saved.pdf'] += b'changed'
            if mode == 'missing': altered.pop('saved.pdf')
            if mode == 'extra': altered['foreign'] = b'x'
            self.assertRaises(ValueError, c.bind_artifacts, trace, self.rows[0], altered)

    def test_real_sdk_package_comparator_checks_all_expanded_parts(self):
        for row in self.rows:
            trace, outputs = complete(row, self.pins, self.bundle)
            result = c.bind_artifacts(trace, row, outputs)
            for name in ('saved.hwpx', 'reopened.hwpx'):
                self.assertEqual(result[name]['whole_sdk_expanded_comparison']['state'], 'exact')
                self.assertTrue(result[name]['whole_sdk_expanded_comparison']['all_expanded_part_bytes_checked'])

    def test_zero_byte_partial_preserved_and_bad_package_not_pass(self):
        trace, _ = complete(self.rows[0], self.pins, self.bundle)
        trace.update(state='effect_unknown', artifacts={})
        value = c.bind_artifacts(trace, self.rows[0], {'saved.hwpx': b''})['saved.hwpx']
        self.assertEqual(value['bytes'], 0); self.assertTrue(value['partial_unqualified_preserved'])
        raw = b'not_a_zip'; trace['artifacts'] = {'saved.hwpx': {'sha256': c.sha(raw), 'bytes': len(raw)}}
        value = c.bind_artifacts(trace, self.rows[0], {'saved.hwpx': raw})['saved.hwpx']
        self.assertEqual(value['whole_sdk_expanded_comparison']['state'], 'rejected')

    def test_read_case_rejects_foreign_path_before_read(self):
        row = {**self.rows[0], 'run_directory': 'foreign'}
        self.assertRaises(ValueError, c.read_case, row, 0, self.pins, self.bundle)

    def test_dispatch_and_current_no_partial_promotion(self):
        with patch.object(c, 'DISPATCH', 'implementation/p09/evidence/never-created-pure-current-fixture.json'):
            result = queue.current({}, self.rows, self.pins, None, self.bundle)
        self.assertEqual((result['state'], result['case_count']), ('NOT_RUN', 0))
        self.assertFalse(result['human_authored_direct_oracle'])
        self.assertFalse(result['native_session_started'])

    def test_actual_native_owner_save_guard_and_no_managed_setter(self):
        library = c.r.bounded(c.ROOT / c.LIBRARY).decode('utf-8')
        self.assertIn("if (-not (Test-P58Owner $Owner)) {throw 'P58_SAVE_OWNER_MISMATCH'}", library)
        self.assertIn('$Owner.documents.Close($false)', library)
        self.assertIn('$Owner.hwp.Quit()', library)
        for forbidden in ('PutFieldText', 'Invoke-P09NativeFormBinding', '.CharShape=', 'Stop-Process', 'taskkill'):
            self.assertNotIn(forbidden, library)

    def test_entire_original_p56_dispatcher_called_no_subset_loop(self):
        body = c.r.bounded(c.ROOT / 'tools/p09/sdk_baseline_native_queue.py').decode('utf-8')
        self.assertIn('q.execute_full_queue(capture.c.predecessor(), capture.c.prior.pins())', body)
        self.assertIn('q.preflight_all(predecessor[', body)
        self.assertNotIn('case_selector', body)
        self.assertNotIn('timeout=', body[body.index('def execute('):body.index('def current(')])


if __name__ == '__main__': unittest.main()
