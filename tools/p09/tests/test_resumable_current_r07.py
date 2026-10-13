"""Synthetic scheduler contracts only; no product runtime receipts created."""
import copy
import json
import unittest

import resumable_current_r07 as v


class ResumableR07Tests(unittest.TestCase):
    def setUp(self):
        self.names = [f'fixture::case_{i:03}' for i in range(249)]
        self.names[-6:] = [v.CORPUS_PREFIX+f'fixture_{i}' for i in range(6)]
        self.exe = copy.deepcopy(v.observed.run.listing.EXE)
        self.expected = {self.exe['path']: self.exe,
                         'crates/fixture/src/lib.rs': dict(path='crates/fixture/src/lib.rs', bytes=3, sha256='a'*64)}
        self.binding = v.identity(self.names, self.expected, self.exe)
        self.pin = dict(path='implementation/p09/evidence/resumable-r07/p190-case-001-attempt-001.json',
                        bytes=123, sha256='b'*64)
        self.case = dict(schema_version=v.SCHEMA, state=v.CASE_PASS, binding=self.binding,
                         selected_test_names=[self.names[0]], test_arguments=v.arguments(self.names[0]),
                         policy=copy.deepcopy(v.c.POLICY), maximum_seconds=1200,
                         cleanup_confirmed=True, owned_tree_empty=True,
                         job_final=dict(active_processes=0, owned_processes=[]),
                         resource_stop_reason=None, stop_reason=None, exit_code=0,
                         writer_authorized=True, worker_created=True, job_assigned=True,
                         actual_job_membership_checked=True, owned_limits_verified=True,
                         full249_current_qualified=False, signed16_current_qualified=False,
                         product_complete=False, PC_freeze_resolved=False, actual_Cargo_SQL_Hangul_run=False,
                         P09_gate='OPEN', A12_gate='OPEN', A13_gate='OPEN', closing_id='batch-001',
                         passed_test_names=[self.names[0]],
                         terminal_summary=dict(passed=1, failed=0, ignored=0, measured=0, filtered_out=248),
                         capture=dict(error_code=None, per_stream_limit_bytes=32768,
                                      complete_streams=True, raw_logs_saved=False))
        self.closing = dict(schema_version=v.CLOSING_SCHEMA, state=v.CLOSING_PASS, binding=self.binding,
                            resource_stop_reason=None, resource_watcher_cleanup_confirmed=True,
                            source_closing_exact=True, source_freeze_before=list(self.expected.values()),
                            source_freeze_after=list(self.expected.values()),
                            case_receipt_pins={self.pin['path']: self.pin}, actual_test_runtime_executed=False,
                            full249_current_qualified=False, signed16_current_qualified=False,
                            product_complete=False, P09_gate='OPEN')
        self.output = ('running 1 test\n'+f'test {self.names[0]} ... ok\n'+
                       'test result: ok. 1 passed; 0 failed; 0 ignored; 0 measured; 248 filtered out; finished in 0.01s\n')

    def accept(self):
        return v.accept_case(self.case, self.names[0], self.binding, self.closing, self.expected, self.pin)

    def plan(self, rows=(), closings=None):
        return v.plan(self.names, self.expected, self.exe, rows, closings)

    def row(self):
        return ('p190-case-001-attempt-001.json', self.case, self.pin)

    def test_plan_exact249_and_six_heavy_are_deferred_not_omitted(self):
        row = self.plan()
        self.assertEqual((row['remaining_individual_cases'], row['remaining_regular_cases'],
                          row['remaining_corpus_cases']), (249, 243, 6))
        self.assertFalse(row['full249_current_qualified'])
        self.assertFalse(row['automatic_retry'])

    def test_accept_one_then_skip_only_that_exact_case(self):
        self.assertTrue(self.accept())
        row = self.plan([self.row()], {'batch-001': self.closing})
        self.assertEqual(row['accepted_test_names'], [self.names[0]])
        self.assertEqual(row['next_index'], 2)
        self.assertEqual(row['remaining_individual_cases'], 248)

    def test_missing_batch_closing_keeps_candidate_not_reusable_pass(self):
        row = self.plan([self.row()])
        self.assertEqual(row['accepted_individual_cases'], 0)
        self.assertEqual(row['successful_candidates_requiring_separate_closing'], 1)
        self.assertEqual(row['next_index'], 2)
        self.assertFalse(row['all249_individual_runtime_qualified'])

    def test_stopped_attempt_preserved_next_attempt_no_automatic_retry(self):
        self.case['state'] = 'STOPPED_NOT_ACCEPTED'
        self.case['stop_reason'] = 'STOP_SUSTAINED_SYSTEM_CPU'
        row = self.plan([self.row()])
        self.assertEqual((row['next_index'], row['next_attempt']), (1, 2))
        self.assertFalse(row['automatic_retry'])

    def test_partial_full48_cannot_be_imported_as_completion(self):
        self.case = dict(state='STOPPED_NOT_ACCEPTED', capture_diagnostics=dict(public_passed_test_count=48))
        with self.assertRaises(ValueError): self.plan([self.row()])

    def test_names_unique_and_no_substring_filter(self):
        self.assertIn('--exact', v.arguments('fixture::case_001'))
        self.names[1] = self.names[0]
        with self.assertRaises(ValueError): self.plan()

    def test_foreign_or_unsafe_test_name_rejected(self):
        for name in ('--ignored', 'fixture;command', '../input', ''):
            with self.assertRaises(ValueError): v.arguments(name)

    def test_source_change_invalidates_old_completion_identity(self):
        self.expected['crates/fixture/src/lib.rs']['sha256'] = 'c'*64
        with self.assertRaises(ValueError): self.plan([self.row()], {'batch-001': self.closing})

    def test_executable_change_or_wrong_current_exe_rejected(self):
        self.exe['sha256'] = 'c'*64
        with self.assertRaises(ValueError): self.plan()

    def test_summary_requires_one_pass_and_248_filtered(self):
        self.assertEqual(v.terminal(self.output, '', self.names[0])['passed'], 1)
        for value in ('247 filtered out', '1 ignored', '1 failed', '2 passed'):
            target = {'247 filtered out':'248 filtered out', '1 ignored':'0 ignored',
                      '1 failed':'0 failed', '2 passed':'1 passed'}[value]
            with self.assertRaises(ValueError): v.terminal(self.output.replace(target, value), '', self.names[0])

    def test_partial_named_ok_without_terminal_summary_rejected(self):
        with self.assertRaises(ValueError): v.terminal(f'test {self.names[0]} ... ok\n', '', self.names[0])

    def test_duplicate_or_foreign_named_ok_rejected(self):
        for extra in (f'test {self.names[0]} ... ok\n', 'test foreign::case ... ok\n'):
            with self.assertRaises(ValueError): v.terminal(extra+self.output, '', self.names[0])

    def test_success_stderr_and_original_overflow_rejected_no_raw_values_saved(self):
        sentinel = 'PRIVATE_DO_NOT_SAVE'
        with self.assertRaises(ValueError) as error: v.terminal(self.output, sentinel, self.names[0])
        self.assertNotIn(sentinel, str(error.exception))
        with self.assertRaises(ValueError): v.terminal('x'*32769, '', self.names[0])

    def test_original_cpu_ram_and_sampling_policy_cannot_be_relaxed(self):
        for key, value in (('emergency_cpu_percent', 100), ('job_memory_limit_percent', 9),
                           ('sample_seconds', 2), ('test_threads', 2)):
            old = self.case['policy'][key]
            self.case['policy'][key] = value
            with self.assertRaises(ValueError): self.accept()
            self.case['policy'][key] = old

    def test_deadline_not_extended(self):
        self.case['maximum_seconds'] = 1201
        with self.assertRaises(ValueError): self.accept()

    def test_exit_stop_cleanup_and_membership_required(self):
        for key, value in (('exit_code', None), ('resource_stop_reason', 'STOP_SUSTAINED_SYSTEM_CPU'),
                           ('cleanup_confirmed', False), ('actual_job_membership_checked', False)):
            old = self.case[key]
            self.case[key] = value
            with self.assertRaises(ValueError): self.accept()
            self.case[key] = old

    def test_final_input_omission_or_changed_pin_rejected(self):
        self.closing['source_freeze_after'] = [self.exe]
        with self.assertRaises(ValueError): self.accept()
        self.closing['source_freeze_after'] = copy.deepcopy(list(self.expected.values()))
        self.closing['source_freeze_after'][1]['sha256'] = 'c'*64
        with self.assertRaises(ValueError): self.accept()

    def test_case_receipt_pin_tamper_rejected(self):
        self.closing['case_receipt_pins'][self.pin['path']] = dict(self.pin, sha256='c'*64)
        with self.assertRaises(ValueError): self.accept()

    def test_duplicate_accepted_case_or_duplicate_attempt_rejected(self):
        with self.assertRaises(ValueError): self.plan([self.row(), self.row()], {'batch-001': self.closing})
        row = ('p190-case-001-attempt-002.json', self.case,
               dict(self.pin, path=self.pin['path'].replace('001.json', '002.json')))
        self.closing['case_receipt_pins'][row[2]['path']] = row[2]
        with self.assertRaises(ValueError): self.plan([self.row(), row], {'batch-001': self.closing})

    def test_unknown_state_and_receipt_path_rejected(self):
        self.case['state'] = 'LOOKS_OK'
        with self.assertRaises(ValueError): self.plan([self.row()])
        self.case['state'] = v.CASE_PASS
        self.pin['path'] = 'target/unreviewed.json'
        with self.assertRaises(ValueError): self.plan([self.row()])

    def test_scope_promotion_never_accepted(self):
        self.case['full249_current_qualified'] = True
        with self.assertRaises(ValueError): self.accept()
        self.case['full249_current_qualified'] = False
        self.closing['product_complete'] = True
        with self.assertRaises(ValueError): self.accept()

    def test_manifest_duplicate_and_path_escape_rejected(self):
        with self.assertRaises(ValueError): v.pins([self.exe, self.exe])
        for path in ('../outside', 'D:/private', '/outside', 'target//input', 'target\\input'):
            with self.assertRaises(ValueError): v.pins([dict(self.exe, path=path)])


if __name__ == '__main__':
    unittest.main()
