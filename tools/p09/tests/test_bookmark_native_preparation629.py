"""Read-only preparation contracts; modeled jobs never qualify an actual session."""
import ast
from contextlib import ExitStack, redirect_stderr
from copy import deepcopy
import io
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import bookmark_native_preparation629 as subject
import inspect_bookmark_native_batch629 as entry


class Reader:
    def __init__(self):
        self.prepared = dict(schema='hwpx-agent.private.bookmark-insertion-prepared-batch/v1',
            state='EIGHT_PRIVATE_CANDIDATE_COPIES_PREPARED_NOT_NATIVE_ENTRY_READY_OR_EXECUTION_AUTHORITY',
            source_receipt=dict(path=subject.PRIOR, sha256=subject.PRIOR_SHA), source=subject.SOURCE_PIN, P09_gate='OPEN')
        for key in ('native_execution_authorized', 'native_entry_ready', 'actual_native_executed',
                    'automatic_execution_or_retry', 'reuse_consumed_001_to010_or_Native008_to011',
                    'initial_display_text_is_computed_or_refreshed',
                    'operating_SQL_scanner_key_custody_or_product_route_qualified',
                    'private_files_are_user_revisions_or_result_ingestion'):
            self.prepared[key] = False
        self.prepared['cases'] = []
        observations = []
        self.pins = {subject.SOURCE: subject.SOURCE_PIN}
        for i in range(1, 9):
            pin = dict(path=subject.DIRECTORY + f'/case-{i:02}.hwpx', bytes=14648, sha256=f'{i:064x}')
            self.pins[pin['path']] = pin
            self.prepared['cases'].append(dict(case_index=i, display=subject.DISPLAYS[(i-1)//2],
                hyperlink=i%2==0, output=pin, output_sha256=pin['sha256'], command_sha256=bytes([i]*32).hex()))
            observations.append(dict(case_index=i, output=deepcopy(pin), receipt=dict(output=dict(command_sha256=[i]*32))))
        self.prior = dict(state='PASS628_CURRENT_STORED_INSERTION8_AND_PRIVATE_OUTPUT8_NOT_CAS_NATIVE_OR_ROUTE',
            cleanup=True, fresh_inputs=930, final_fresh_hashes=930,
            actual_current_stored_observation=dict(observations=observations))
        self.snapshots = {subject.PRIOR: dict(sha256=subject.PRIOR_SHA)}
    def json(self, path):
        return self.prepared if path == subject.PREPARED else self.prior
    def pin(self, path):
        return self.pins[path]


class Contracts(unittest.TestCase):
    def setUp(self):
        self.reader = Reader()
    def validate(self):
        return subject.validate_prepared(self.reader, lambda v: v)
    def reject(self, code):
        with self.assertRaisesRegex(ValueError, code):
            self.validate()
    def test_01_whole_eight_is_preparation_not_a_native_or_product_permit(self):
        result = self.validate()
        self.assertEqual(result['actual_file_count'], 8)
        self.assertIs(result['native_entry_ready'], False)
        self.assertIs(result['native_execution_authorized'], False)
        self.assertIs(result['initial_result_evaluated'], False)
    def test_02_subset_duplicate_or_wrong_order_fails(self):
        original = deepcopy(self.reader.prepared['cases'])
        for value in (original[:-1], original[::-1], [original[0]]*8):
            self.reader.prepared['cases'] = value
            self.reject('WHOLE_EIGHT|EXACT_CASE')
    def test_03_boolean_case_and_integer_hyperlink_do_not_equal_typed_modes(self):
        self.reader.prepared['cases'][0]['case_index'] = True
        self.reject('EXACT_CASE')
        self.reader.prepared['cases'][0]['case_index'] = 1
        self.reader.prepared['cases'][0]['hyperlink'] = 0
        self.reject('EXACT_CASE')
    def test_04_wrong_display_pair_fails(self):
        self.reader.prepared['cases'][2]['display'] = 'page'
        self.reject('EXACT_CASE')
    def test_05_receipt_hash_state_or_final_closure_cannot_be_relabelled(self):
        self.reader.snapshots[subject.PRIOR]['sha256'] = '0'*64
        self.reject('EXACT_STORED')
        self.reader.snapshots[subject.PRIOR]['sha256'] = subject.PRIOR_SHA
        self.reader.prior['final_fresh_hashes'] = 929
        self.reject('EXACT_STORED')
    def test_06_changed_original_source_fails(self):
        self.reader.pins[subject.SOURCE] = dict(subject.SOURCE_PIN, sha256='0'*64)
        self.reject('CURRENT_ORIGINAL')
    def test_07_actual_candidate_change_fails_even_when_manifest_is_unchanged(self):
        path = subject.DIRECTORY+'/case-06.hwpx'
        self.reader.pins[path] = dict(self.reader.pins[path], sha256='0'*64)
        self.reject('CURRENT_PREPARED')
    def test_08_manifest_and_file_cannot_replace_original_receipt_output(self):
        case = self.reader.prepared['cases'][0]
        case['output']['sha256'] = case['output_sha256'] = '0'*64
        self.reject('EXACT_CURRENT_PRODUCT')
    def test_09_old_namespace_or_arbitrary_file_path_fails(self):
        self.reader.prepared['cases'][0]['output']['path'] = 'implementation/p09/evidence/private/old/saved.hwpx'
        self.reject('EXACT_CURRENT_PRODUCT')
    def test_10_each_false_authority_flag_is_required(self):
        for key in [k for k, v in self.reader.prepared.items() if v is False]:
            self.reader.prepared[key] = True
            self.reject('PREPARED_IS_NOT_AUTHORITY')
            self.reader.prepared[key] = False
    def test_11_command_hash_is_bound_to_actual_stored_output_not_only_manifest(self):
        self.reader.prepared['cases'][0]['command_sha256'] = '0'*64
        self.reject('EXACT_CURRENT_PRODUCT')
    def modeled_current(self, denied=False, drift=False, stop=False):
        stack = ExitStack()
        self.addCleanup(stack.close)
        identity = dict(process_id=123, creation_filetime_100ns='456', session_id=1)
        stack.enter_context(patch.object(subject.inspection, 'current_identity',
            side_effect=[identity, dict(identity, process_id=124) if drift else identity]))
        observed = dict(all_observed_prerequisites_passed=not denied, failed_prerequisites=['caller_lifecycle_native_safe'] if denied else [])
        stack.enter_context(patch.object(subject.inspection.prerequisites, 'inspect', return_value=observed))
        stack.enter_context(patch.object(subject.inspection.prerequisites.startup, 'parent_without_prompt_kill', return_value=dict(job_present=False)))
        jobs = stack.enter_context(patch.object(subject.inspection, 'empty_resource_layout', return_value=dict(empty_jobs_closed=True)))
        current = Mock()
        checkpoint = Mock(side_effect=ValueError('STOP_SYSTEM_CPU') if stop else None)
        return lambda: subject.inspect_current(object(), checkpoint, lambda: {}, current), jobs, current
    def test_12_modeled_external_success_is_never_session_or_execution_authority(self):
        call, jobs, current = self.modeled_current()
        result = call()
        self.assertIs(result['external_jobless_prerequisites_observed'], True)
        for key in ('process_created', 'COM_activated', 'document_opened_or_saved',
                    'permission_dialog_requested', 'native_startup_qualified', 'native_execution_authorized', 'native_entry_ready'):
            self.assertIs(result[key], False)
        jobs.assert_called_once()
        self.assertEqual(current.call_count, 2)
    def test_13_job_denial_does_not_create_empty_jobs_or_touch_hwp(self):
        call, jobs, _ = self.modeled_current(denied=True)
        result = call()
        self.assertIs(result['external_jobless_prerequisites_observed'], False)
        self.assertIsNone(result['empty_resource_layout'])
        jobs.assert_not_called()
    def test_14_same_creator_drift_rejects(self):
        call, _, _ = self.modeled_current(drift=True)
        with self.assertRaisesRegex(ValueError, 'SAME_KERNEL_CREATOR'):
            call()
    def test_15_resource_stop_propagates_before_any_runtime_or_job_operation(self):
        call, jobs, current = self.modeled_current(stop=True)
        with self.assertRaisesRegex(ValueError, 'STOP_SYSTEM_CPU'):
            call()
        jobs.assert_not_called()
        current.assert_not_called()
    def test_16_cli_has_no_execute_generation_subset_path_or_retry_mode(self):
        with redirect_stderr(io.StringIO()):
            for args in ([], ['--execute'], ['--inspect-only', '--case', '1'],
                         ['--inspect-only', '--retry'], ['--inspect-only', '--output', 'PRIVATE']):
                with self.assertRaises(SystemExit):
                    entry.parser().parse_args(args)
        self.assertTrue(entry.parser().parse_args(['--inspect-only']).inspect_only)
    def test_17_sources_do_not_launch_native_or_worker_or_reuse_sdk_insertion(self):
        root = Path(__file__).resolve().parents[3]
        forbidden = {'CreateProcessW', 'ResumeThread', 'Popen', 'run', 'system', 'CoCreateInstance',
                     'AssignProcessToJobObject', 'create_suspended', 'resume', 'bind_owner', 'admit',
                     'start_waiting', 'kill', 'issue_handoff', 'execute', 'sdk_insert'}
        for path in (subject.SELF, entry.SELF):
            tree = ast.parse((root/path).read_text(encoding='utf-8'))
            calls = {n.func.attr if isinstance(n.func, ast.Attribute) else n.func.id for n in ast.walk(tree)
                     if isinstance(n, ast.Call) and isinstance(n.func, (ast.Name, ast.Attribute))}
            self.assertFalse(calls & forbidden)
    def test_18_errors_do_not_expose_raw_values_and_existing_output_is_not_overwritten(self):
        self.assertEqual(subject.safe_code(OSError('PRIVATE VALUE')), 'P629_FAILURE_NO_RAW_VALUES')
        root = Path(__file__).resolve().parents[3]
        with self.assertRaisesRegex(ValueError, 'IMMUTABLE_OUTPUT_NO_REPLAY'):
            subject.require_absent(root, subject.PREPARED)


if __name__ == '__main__':
    stream = io.StringIO()
    result = unittest.TextTestRunner(stream=stream).run(unittest.defaultTestLoader.loadTestsFromTestCase(Contracts))
    print(json.dumps(dict(run=result.testsRun, errors=len(result.errors), failures=len(result.failures),
                          skipped=len(result.skipped), failed_tests=[test.id().rsplit('.', 1)[-1]
                          for test, _ in result.errors + result.failures])), flush=True)
    raise SystemExit(0 if result.wasSuccessful() and not result.skipped else 2)
