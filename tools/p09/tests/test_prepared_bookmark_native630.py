"""New prepared-file wire contracts; callbacks never simulate real Native effects."""
import io
import json
from contextlib import redirect_stderr
from pathlib import Path
import sys
from types import SimpleNamespace as NS
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import prepared_bookmark_native630 as subject
import run_prepared_bookmark_native630 as entry


def frame(step='prepare_slot', **changes):
    value = dict(schema_version=subject.REQUEST, sequence=1, case_index=1, operation='checkpoint', step=step)
    value.update(changes)
    return json.dumps(value)


class Contracts(unittest.TestCase):
    def test_01_all_public_stages_map_bijectively_to_unchanged_resource_schedule(self):
        self.assertEqual(len(subject.STEPS), 16)
        self.assertEqual(tuple(subject.LEGACY.values()), subject.base.batch.original.original.STEPS)
        for step in subject.STEPS:
            public, internal = subject.translate_request(frame(step))
            self.assertEqual(public['step'], step)
            self.assertEqual(internal['step'], subject.LEGACY[step])
            self.assertEqual(internal['schema_version'], subject.base.batch.original.REQUEST)
        self.assertNotIn('sdk_insert', subject.STEPS)
        self.assertEqual(subject.LEGACY['initial_pdf'], 'sdk_insert')
    def test_02_legacy_and_unknown_schema_or_step_is_rejected(self):
        for raw in (frame(schema_version=subject.base.batch.original.REQUEST), frame('sdk_insert'), frame('refresh'), frame('other')):
            with self.assertRaises(ValueError):
                subject.translate_request(raw)
    def test_03_no_boolean_numeric_ids_subset_or_overflow(self):
        for changes in (dict(case_index=True), dict(sequence=True), dict(case_index=0), dict(case_index=9), dict(sequence=257)):
            with self.assertRaises(ValueError):
                subject.translate_request(frame(**changes))
    def test_04_unknown_keys_arbitrary_paths_or_operation_not_accepted(self):
        for changes in (dict(path='PRIVATE'), dict(approval=True), dict(operation='execute'), dict(operation='restart')):
            with self.assertRaises(ValueError):
                subject.translate_request(frame(**changes))
    def test_05_wire_size_duplicate_key_and_newline_fail_closed(self):
        for raw in (frame()+'\n', frame()[:-1]+',"case_index":1}', 'x'*4097):
            with self.assertRaises(ValueError):
                subject.translate_request(raw)
    def test_06_admission_keeps_original_exact_owner_shape(self):
        value = dict(schema_version=subject.REQUEST, sequence=3, case_index=1, operation='admit_owner', identity={}, window_handle=123)
        with self.assertRaises(ValueError):
            subject.translate_request(json.dumps(value))
    def test_07_finish_is_not_an_execution_permit(self):
        value = dict(schema_version=subject.REQUEST, sequence=19, case_index=1, operation='finish', case_status='returned')
        public, internal = subject.translate_request(json.dumps(value))
        self.assertEqual(internal['case_status'], 'returned')
        self.assertNotIn('native_execution_authorized', public)
    def test_08_host_does_not_forward_unrecognized_wire_or_continue_after_it(self):
        host = object.__new__(subject.Host)
        host.scope = NS(stopped=False)
        host.protocol = NS(protocol=NS(stopped=False))
        with patch.object(subject.base.batch.FixedEightHost, 'respond') as downstream:
            with self.assertRaises(ValueError):
                host.respond(frame('sdk_insert'))
            downstream.assert_not_called()
        self.assertTrue(host.scope.stopped)
        self.assertTrue(host.protocol.protocol.stopped)
    def test_09_host_reply_has_distinct_purpose_without_native_effect_claim(self):
        host = object.__new__(subject.Host)
        response = dict(schema_version=subject.base.batch.original.RESPONSE, sequence=1, case_index=1,
                        acknowledged=True, error_code=None, owner_descriptor=None, native_execution_authorized=False, p09_complete=False)
        with patch.object(subject.base.batch.FixedEightHost, 'respond', return_value=json.dumps(response)) as call:
            actual = json.loads(host.respond(frame('initial_pdf')))
            self.assertEqual(json.loads(call.call_args.args[0])['step'], 'sdk_insert')
        self.assertEqual(actual['schema_version'], subject.RESPONSE)
        self.assertIs(actual['native_execution_authorized'], False)
        self.assertIs(actual['p09_complete'], False)
    def test_10_new_eight_paths_are_fixed_disjoint_and_immutable(self):
        paths = [subject.directory(i) for i in range(1, 9)]
        self.assertEqual(len(set(paths)), 8)
        self.assertTrue(all('prepared-bookmark630-native001-c' in p and 'crossref-bookmark-native-' not in p for p in paths))
        for value in (True, 0, 9, '1'):
            with self.assertRaises(ValueError):
                subject.directory(value)
    def test_11_cli_has_one_fixed_capture_and_no_preflight_retry_or_generation_selector(self):
        with redirect_stderr(io.StringIO()):
            for args in ([], ['--execute'], ['--execute-prepared-eight-once', '--retry'],
                         ['--execute-prepared-eight-once', '--case', '1'], ['--execute-prepared-eight-once', '--generation', '2']):
                with self.assertRaises(SystemExit):
                    entry.parser().parse_args(args)
        self.assertTrue(entry.parser().parse_args(['--execute-prepared-eight-once']).execute_prepared_eight_once)
    def test_12_unchanged_host_lifecycle_functions_are_reused_not_reimplemented(self):
        self.assertIs(subject.Host.__mro__[1], subject.base.batch.FixedEightHost)
        self.assertIs(subject.Worker.start_fixed_worker, subject.worker_base.FixedWorker.start_fixed_worker)
        self.assertIs(subject.Cases.end, subject.base.CaseInputs.end)
        self.assertIs(subject.Handler.current_native, subject.base.BatchHandler.current_native)
    def test_13_all_eight_ordered_resource_frames_return_without_claiming_semantics(self):
        legacy = subject.base.batch.original.original
        callbacks = []
        protocol = legacy.HostProtocol(lambda i, step: callbacks.append((i, step)), lambda *a: None, lambda *a: None)
        sequence = 0
        for index in range(1, 9):
            for operation, step in legacy.FLOW:
                sequence += 1
                value = dict(schema_version=subject.REQUEST, sequence=sequence, case_index=index, operation=operation)
                if operation == 'checkpoint':
                    value['step'] = subject.STEPS[legacy.STEPS.index(step)]
                else:
                    # Decode still uses the exact original owner validator.
                    value.update(identity={}, window_handle=1)
                if operation == 'admit_owner':
                    with patch.object(legacy.limits, 'validate_identity', return_value=1):
                        _, internal = subject.translate_request(json.dumps(value))
                        reply = json.loads(protocol.respond(json.dumps(dict(internal, schema_version=legacy.REQUEST))))
                else:
                    _, internal = subject.translate_request(json.dumps(value))
                    reply = json.loads(protocol.respond(json.dumps(dict(internal, schema_version=legacy.REQUEST))))
                self.assertTrue(reply['acknowledged'])
            sequence += 1
            value = dict(schema_version=subject.REQUEST, sequence=sequence, case_index=index, operation='finish', case_status='returned')
            _, internal = subject.translate_request(json.dumps(value))
            self.assertTrue(json.loads(protocol.respond(json.dumps(dict(internal, schema_version=legacy.REQUEST))))['acknowledged'])
        self.assertEqual(len(callbacks), 128)
        self.assertTrue(protocol.summary()['all_eight_callback_cases_returned'])
        self.assertFalse(protocol.summary()['native_execution_attested'])
    def test_14_case_boundary_cannot_advance_with_a_live_or_unclosed_predecessor(self):
        cases = object.__new__(subject.Cases)
        cases.current = NS()
        cases.rows = []
        cases.host = NS(scope=NS(), protocol=NS(protocol=NS()))
        with self.assertRaises(ValueError):
            cases.between(1)


if __name__ == '__main__':
    stream = io.StringIO()
    result = unittest.TextTestRunner(stream=stream).run(unittest.defaultTestLoader.loadTestsFromTestCase(Contracts))
    print(json.dumps(dict(run=result.testsRun, errors=len(result.errors), failures=len(result.failures), skipped=len(result.skipped),
        failed_tests=[test.id().rsplit('.', 1)[-1] for test, _ in result.errors+result.failures])), flush=True)
    raise SystemExit(0 if result.wasSuccessful() and not result.skipped else 2)
