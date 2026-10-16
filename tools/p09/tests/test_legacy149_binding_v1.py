import copy
import hashlib
import unittest

MODULE = BINDING = ROWS = PIN = SCOPE = CHECK = CARRIERS = METHODS = PROJECTION = PRIOR = XZ = None
READER = SOURCE_READER = CHUNK = None


class Tests(unittest.TestCase):
    def bound(self): return BINDING.Binding(copy.deepcopy(ROWS), PIN, next_case=165)
    def required(self): return SCOPE.pins([r['semantic_original_pin'] for r in ROWS]+[PIN])

    def test_all_nonconstructor_and_Projection_methods_retained(self):
        self.assertTrue(all(vars(BINDING.Binding).get(n) is f for n, f in METHODS.items()))
        self.assertTrue(all(vars(BINDING.source.Projection).get(n) is f for n, f in PROJECTION.items()))

    def test_all75_projection_and_extra_source_retained(self):
        b = self.bound(); rows = self.required()
        extra = dict(path=MODULE.SELF, bytes=1, sha256='a'*64); rows[extra['path']] = extra
        p, _ = b.project(rows, CHECK)
        self.assertEqual(b.descriptors(), ROWS)
        self.assertEqual(len(p.semantic_pins), len(p.physical_pins))
        self.assertEqual(dict(p.semantic_pins[extra['path']]), extra)
        for r in MODULE.RECORDS:
            self.assertNotIn(r['original']['path'], p.physical_pins)
            self.assertEqual(dict(p.physical_pins[r['physical']['path']]), r['physical'])

    def test_distinct_failure_reasons_unknown_execution_and_all_old_roles_survive(self):
        b = self.bound(); p, _ = b.project(self.required(), CHECK); row = b.representation(p)
        role = row['legacy149_validation_failures_provenance']
        self.assertEqual(role, MODULE.ROLE)
        self.assertEqual([r['original_stop_reason'] for r in role['records']], ['OWNED_RUNNER_FAILURE', 'STOP_LOW_AVAILABLE_RAM'])
        self.assertTrue(all(r['actual_failed_product_child_executed'] is None and r['original_failure_promoted'] is False for r in role['records']))
        self.assertIs(row['same_case_failed165_run007_provenance']['actual_failed_product_child_executed'], True)
        self.assertIsNone(row['same_case_failed165_run008_provenance']['actual_failed_product_child_executed'])
        self.assertEqual(len(row['historical_validation_failures_provenance']['records']), 2)
        self.assertIsNone(row['legacy154_validation_failure_provenance']['actual_failed_product_child_executed'])

    def test_both_actual_new_codecs_restore_exact_original_bytes_and_guard_first(self):
        self.bound()
        for r, encoded in zip(MODULE.RECORDS, CARRIERS):
            raw = BINDING.source.codec.decode(encoded, CHECK)
            self.assertEqual((len(raw), hashlib.sha256(raw).hexdigest()), (r['original']['bytes'], r['original']['sha256']))
        def stop(): raise ValueError('ORIGINAL_STOP')
        with self.assertRaisesRegex(ValueError, 'ORIGINAL_STOP'): BINDING.source.codec.decode(CARRIERS[0], stop)

    def test_missing_duplicate_prior_and_either_new_tamper_rejected(self):
        for kind in ('missing', 'duplicate', 'prior', 'first', 'second', 'order'):
            rows = copy.deepcopy(ROWS)
            if kind == 'missing': rows.pop()
            elif kind == 'duplicate': rows[0] = copy.deepcopy(rows[1])
            elif kind == 'prior': rows[0]['physical_envelope_pin']['sha256'] = '0'*64
            elif kind == 'order': rows[-2:] = rows[-2:][::-1]
            else: rows[-2 if kind == 'first' else -1]['semantic_original_pin']['sha256'] = '0'*64
            with self.assertRaises(ValueError): BINDING.Binding(rows, PIN, next_case=165)

    def test_wrong_case_either_missing_original_and_manifest_tamper_rejected(self):
        for case in (164, True):
            with self.assertRaises(ValueError): BINDING.Binding(ROWS, PIN, next_case=case)
        b = self.bound()
        for r in MODULE.RECORDS:
            rows = self.required(); rows.pop(r['original']['path'])
            with self.assertRaises(ValueError): b.project(rows, CHECK)
        rows = self.required(); rows[PIN['path']] = dict(PIN, sha256='0'*64)
        with self.assertRaises(ValueError): b.project(rows, CHECK)

    def test_both_exact_aliases_reconcile_but_physical_or_semantic_conflict_rejects(self):
        b = self.bound(); rows = self.required()
        for r in MODULE.RECORDS: rows[r['physical']['path']] = r['physical']
        semantic, _ = b.semantic_union(rows, CHECK)
        for r in MODULE.RECORDS:
            self.assertEqual(semantic[r['original']['path']], r['original'])
            bad = copy.deepcopy(rows); bad[r['physical']['path']]['sha256'] = '0'*64
            with self.assertRaises(ValueError): b.semantic_union(bad, CHECK)
            bad = copy.deepcopy(rows); bad[r['original']['path']]['bytes'] = 1
            with self.assertRaises(ValueError): b.semantic_union(bad, CHECK)

    def test_generic_metadata_source_exe_fixture_and_current_product_alias_denied(self):
        self.bound(); r = MODULE.RECORDS[0]
        for path in ('tools/p09/source.py', 'target/product.exe', 'implementation/p09/fixtures/source.json',
            MODULE.PREFIX+'current-runtime-run009.v1.json', 'implementation/p09/evidence/other-legacy.json'):
            with self.assertRaises(ValueError): BINDING.source.descriptor(dict(r['original'], path=path), r['physical'], next_case=165)

    def test_changed_role_stop_reason_execution_assertion_and_boolean_coercion_denied(self):
        for field, value in (('original_failure_promoted', True), ('original_failure_promoted', 0),
            ('source_role', 'prebody_no_worker'), ('original_stop_reason', 'STOP_DURATION_LIMIT'),
            ('actual_failed_product_child_executed', False), ('actual_failed_product_child_executed', True)):
            for index in (0, 1):
                role = copy.deepcopy(MODULE.ROLE); role['records'][index][field] = value
                with self.assertRaises(ValueError): MODULE.install(BINDING, PRIOR, role, XZ, physical_run=9)

    def test_other_run_missing_prior_tamper_and_reinstall_rejected(self):
        for run in (8, True):
            with self.assertRaises(ValueError): MODULE.install(BINDING, PRIOR, MODULE.ROLE, XZ, physical_run=run)
        with self.assertRaises(ValueError): MODULE.install(BINDING, PRIOR[:-1], MODULE.ROLE, XZ, physical_run=9)
        with self.assertRaises(ValueError): MODULE.install(BINDING, PRIOR, MODULE.ROLE, XZ, physical_run=9)

    def test_every_prior_descriptor_and_original_special_codec_retained(self):
        self.bound()
        for r in PRIOR:
            self.assertEqual(BINDING.source.descriptor(r['semantic_original_pin'], r['physical_envelope_pin'], next_case=165), r)
        raw = BINDING.xz_original_codec.encode(b'old special', CHECK)
        self.assertEqual(BINDING.source.codec.decode(raw, CHECK), b'old special')

    def test_swapping_fixed_physical_files_or_noninteger_sizes_is_rejected(self):
        self.bound()
        for index, r in enumerate(MODULE.RECORDS):
            for bad in (MODULE.RECORDS[1-index]['physical'], dict(r['physical'], bytes=True), dict(r['physical'], sha256='0'*64)):
                with self.assertRaises(ValueError): BINDING.source.descriptor(r['original'], bad, next_case=165)

    def test_actual_preparation_reader_preserves_source_and_every_prior_MRO_layer(self):
        expected = list(SOURCE_READER.__mro__)
        self.assertIs(type(READER)._source, SOURCE_READER._source)
        before = type(READER).__mro__[1:]
        self.assertEqual([cls for cls in before if cls.__name__ != 'ChunkLeaf'], expected)
        self.assertEqual(sum(cls.__name__ == 'ChunkLeaf' for cls in before), 1)

    def test_actual_preparation_workspace_fresh_reads_no_cache_or_active_lease(self):
        row = CHUNK.summary(READER)
        self.assertEqual(row['workspace_allocations'], 1)
        self.assertEqual(row['workspace_bytes'], 65536)
        self.assertGreater(row['readinto_completed'], 0)
        self.assertEqual(row['leases'], row['lease_returns'])
        self.assertFalse(row['active_lease'])
        self.assertFalse(row['file_bytes_or_hash_or_JSON_cache'])
        self.assertTrue(row['original_checkpoints_pacing_parse_budget_and_final_hashes_preserved'])
