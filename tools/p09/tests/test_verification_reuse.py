"""Synthetic reuse-dispatch tests; no real product, files or queue writes."""
import copy
import unittest

MODULE = None


class ReuseTests(unittest.TestCase):
    def setUp(self):
        self.m = MODULE
        names = list(self.m.REQUIRED) + ['implementation/p09/evidence/test-%03d.json' % i
            for i in range(self.m.DEPENDENCIES - len(self.m.REQUIRED))]
        self.rows = [dict(path=name, bytes=1, sha256='a' * 64) for name in names]
        self.row = dict(state=self.m.STATE, contracts=dict(run=16, errors=0, failures=0, skipped=0),
            descriptor_count=162, fresh_inputs=185, final_fresh_hashes=185, cleanup_confirmed=True,
            accepted_count_delta=0, GO_authorized=False, Native009_replayed=False,
            worker_process_engine_Job_Frame_or_Native_executed=False,
            current_full_runtime_scope_or_helper64_qualified=False,
            actual_metadata_Frame_shared_decoder5_qualified=False,
            original_limits_or_preparation_CPU_policy_changed=False, subprocess_creation_attempts=0,
            actual_current162_original_decoder_completed=True, reconstruction_JSON_file_opens=0,
            source_pins=self.rows)
        for key, pin in zip(('manifest_pin', 'wire_pin', 'bootstrap_pin', 'data_source_module_pin'), self.rows):
            self.row[key] = dict(pin)

    def reader(self):
        row = copy.deepcopy(self.row)
        m = self.m
        class Reader:
            def __init__(self):
                self.snapshots = {}
                self.reads = []
                self.final_fresh_hashes = 0
            def json(self, name):
                self.reads.append(name)
                self.snapshots[name] = copy.deepcopy(m.PROOF)
                return copy.deepcopy(row)
            def pin(self, name):
                self.reads.append(name)
                pin = next(p for p in row['source_pins'] if p['path'] == name)
                self.snapshots[name] = dict(pin)
                return dict(pin)
            def finish(self):
                self.final_fresh_hashes = len(self.snapshots)
        return Reader()

    def test_exact_closed_result(self):
        self.assertEqual(len(self.m.dependencies(self.row)), 185)

    def test_every_dependency_once_without_recursing(self):
        reader = self.reader()
        out = self.m.check(reader)
        self.assertEqual(len(reader.reads), 186)
        self.assertEqual(len(set(reader.reads)), 186)
        self.assertEqual(out['preparation_contracts_reexecuted'], 0)

    def test_no_promoted_acceptance_environment_or_budget(self):
        out = self.m.check(self.reader())
        for key in ('GO_authorized', 'product_executed', 'current_runtime_budget_reused',
                    'prior_resource_measurements_reused', 'current_environment_qualified',
                    'Native_source_frame_qualified', 'whole_current_source_scope_changed'):
            self.assertIs(out[key], False)
        self.assertEqual(out['accepted_count_delta'], 0)
        self.assertEqual(out['evidence_files_created'], 0)

    def test_dependency_changed(self):
        reader = self.reader()
        original = reader.pin
        def changed(name):
            return dict(original(name), sha256='b' * 64)
        reader.pin = changed
        with self.assertRaisesRegex(ValueError, 'DEPENDENCY_CHANGED'):
            self.m.check(reader)

    def test_missing_dependency(self):
        reader = self.reader()
        def missing(name):
            raise FileNotFoundError()
        reader.pin = missing
        with self.assertRaises(FileNotFoundError):
            self.m.check(reader)

    def test_wrong_receipt_hash(self):
        reader = self.reader()
        original = reader.json
        def changed(name):
            value = original(name)
            reader.snapshots[name]['sha256'] = 'b' * 64
            return value
        reader.json = changed
        with self.assertRaisesRegex(ValueError, 'IMMUTABLE_PROOF_HASH'):
            self.m.check(reader)

    def test_input_not_mutated(self):
        before = copy.deepcopy(self.row)
        self.m.dependencies(self.row)
        self.assertEqual(self.row, before)

    def test_missing_or_duplicate_inputs(self):
        for change in ('missing', 'duplicate', 'case_alias'):
            row = copy.deepcopy(self.row)
            if change == 'missing':
                row['source_pins'].pop()
            else:
                row['source_pins'][-1] = dict(row['source_pins'][0])
                if change == 'case_alias':
                    row['source_pins'][-1]['path'] = row['source_pins'][-1]['path'].upper()
            with self.subTest(change=change), self.assertRaises(ValueError):
                self.m.dependencies(row)

    def test_failed_or_partial_results_never_reused(self):
        for key, value in (('state', 'FAILED'), ('final_fresh_hashes', 184),
                           ('cleanup_confirmed', False), ('actual_current162_original_decoder_completed', False)):
            row = copy.deepcopy(self.row)
            row[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.m.dependencies(row)

    def test_bool_int_not_equivalent(self):
        for key, value in (('accepted_count_delta', False), ('fresh_inputs', True),
                           ('GO_authorized', 0), ('cleanup_confirmed', 1)):
            row = copy.deepcopy(self.row)
            row[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.m.dependencies(row)

    def test_inexact_artifact_not_reused(self):
        row = copy.deepcopy(self.row)
        row['wire_pin']['sha256'] = 'b' * 64
        with self.assertRaisesRegex(ValueError, 'ALL_ACTUAL_ARTIFACT_PINS'):
            self.m.dependencies(row)

    def test_failed_contract_not_reused(self):
        for key in ('errors', 'failures', 'skipped'):
            row = copy.deepcopy(self.row)
            row['contracts'][key] = 1
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.m.dependencies(row)

    def test_unsafe_paths(self):
        for name in ('../x', 'tools//x', 'C:/x', 'tools/x.', 'tools/x ', 'tools/x\n'):
            row = copy.deepcopy(self.row)
            row['source_pins'][-1]['path'] = name
            with self.subTest(name=name), self.assertRaises(ValueError):
                self.m.dependencies(row)

    def test_required_source_missing(self):
        row = copy.deepcopy(self.row)
        row['source_pins'][0]['path'] = 'tools/p09/not-the-qualified-source.py'
        with self.assertRaisesRegex(ValueError, 'CLOSED_EXISTING_DEPENDENCIES'):
            self.m.dependencies(row)

    def test_no_result_returned_before_fresh_closing(self):
        reader = self.reader()
        def failed_finish():
            raise ValueError('INPUT_CHANGED_DURING_CLOSING')
        reader.finish = failed_finish
        class Guard:
            def check(self, force=False):
                raise AssertionError('must not sample after failed closing')
        with self.assertRaisesRegex(ValueError, 'INPUT_CHANGED_DURING_CLOSING'):
            self.m.complete(reader, Guard())

    def test_final_resource_stop_never_reused(self):
        reader = self.reader()
        class Guard:
            def check(self, force=False):
                if force is not True:
                    raise AssertionError('final sample must be distinct/forced')
                raise ValueError('RESOURCE_STOP')
        with self.assertRaisesRegex(ValueError, 'RESOURCE_STOP'):
            self.m.complete(reader, Guard())

    def test_complete_requires_all_closing_hashes(self):
        reader = self.reader()
        reader.finish = lambda: None
        class Guard:
            def check(self, force=False):
                pass
        with self.assertRaisesRegex(ValueError, 'ALL_CLOSING_HASHES'):
            self.m.complete(reader, Guard())
