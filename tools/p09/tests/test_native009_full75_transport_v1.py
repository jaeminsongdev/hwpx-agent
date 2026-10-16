import copy
import hashlib
import unittest

MODULE = API = HINT = WIRE = GRAPH = ROWS = CHECK = BOUNDED = LINKED = OBSERVED = BASIS = CODE = BASIS_BYTES = READER = CHUNK = SOURCE = None


class Tests(unittest.TestCase):
    def test_all75_original_private_worker_Frame_and_oracle_graph(self):
        self.assertEqual(GRAPH.binding.descriptors(), ROWS)
        for owner in (GRAPH.worker, GRAPH.frames, GRAPH.full_oracle):
            self.assertIs(owner.source if owner is GRAPH.worker else owner.binding_module, GRAPH.binding_module)

    def test_all_four_count_slots_and_suffix_have_whole_code_inverses(self):
        for proof in (API.inner_count_proof, API.middle_count_proof, API.top_count_proof, API.engine_proof):
            self.assertEqual((proof['old'], proof['new']), (73, 75)); self.assertTrue(proof['whole_code_inverse'])
            self.assertTrue(proof['original_defaults_closure_and_globals_retained'])
        self.assertEqual((API.suffix_proof['old'], API.suffix_proof['new']), ('.compact.v4.json', '.compact.v5.json'))
        self.assertTrue(API.suffix_proof['whole_code_inverse'])

    def check_closure(self, before, after, old_inner, new_inner):
        self.assertEqual(before.__code__.co_filename, after.__code__.co_filename)
        index = list(before.__code__.co_freevars).index('reconstruction')
        self.assertIs(before.__closure__[index].cell_contents, old_inner)
        self.assertIs(after.__closure__[index].cell_contents, new_inner)
        for slot in range(len(before.__closure__)):
            if slot != index: self.assertIs(before.__closure__[slot], after.__closure__[slot])

    def test_middle_changes_only_declared_inner_dependency(self):
        self.check_closure(API.original_middle, API.revised_middle, API.original_inner, API.revised_inner)
        self.assertTrue(API.middle_closure_proof['entire_closure_inverse'])

    def test_top_changes_only_declared_middle_dependency(self):
        self.check_closure(API.original_top, API.revised_top, API.original_middle, API.revised_middle)
        self.assertTrue(API.top_closure_proof['entire_closure_inverse'])

    def test_top_dependency_rejects_wrong_source_body_or_expected_closure(self):
        with self.assertRaises(ValueError): MODULE.top_dependency(API.original_middle, API.original_inner, API.revised_inner)
        with self.assertRaises(ValueError): MODULE.top_dependency(API.original_top, None, API.revised_middle)

    def test_original_engine_composed_once_and_product10_not_executed(self):
        self.assertEqual((LINKED.state.attempts, LINKED.state.calls), (0, 0)); self.assertFalse(LINKED.state.completed)
        self.assertEqual(LINKED.window.WINDOW.SECONDS, 10); self.assertIs(LINKED.engine.worker, LINKED.original_worker)

    def test_every_prior_and_new_failure_declaration_is_mandatory(self):
        for field in (MODULE.FIELD, 'legacy154_validation_failure_declaration', 'native007_executed_failure_declaration',
            'legacy_validation_failure_declarations', 'native008_failed_capture_declaration', 'closed_prebody_source_declaration'):
            self.assertIn(field, HINT); hint = copy.deepcopy(HINT); hint.pop(field)
            with self.assertRaises(ValueError): API.validate(hint)

    def test_distinct_stop_reasons_and_unknown_execution_never_relabel(self):
        role = HINT[MODULE.FIELD]
        self.assertEqual([r['original_stop_reason'] for r in role['records']], ['OWNED_RUNNER_FAILURE', 'STOP_LOW_AVAILABLE_RAM'])
        self.assertTrue(all(r['actual_failed_product_child_executed'] is None and r['original_failure_promoted'] is False for r in role['records']))
        self.assertIs(HINT['native007_executed_failure_declaration']['actual_failed_product_child_executed'], True)
        self.assertIsNone(HINT['native008_failed_capture_declaration']['actual_failed_product_child_executed'])
        self.assertIsNone(HINT['legacy154_validation_failure_declaration']['actual_failed_product_child_executed'])
        for index in (0, 1):
            for field, value in (('actual_failed_product_child_executed', False), ('actual_failed_product_child_executed', True),
                ('original_failure_promoted', 0), ('original_stop_reason', 'STOP_DURATION_LIMIT')):
                hint = copy.deepcopy(HINT); hint[MODULE.FIELD]['records'][index][field] = value
                with self.assertRaises(ValueError): API.validate(hint)

    def test_wrong_context_extra_field_and_old_suffix_are_denied(self):
        for key, value in (('index', 164), ('index', True), ('run', 8), ('unexpected', True)):
            hint = copy.deepcopy(HINT); hint[key] = value
            with self.assertRaises(ValueError): API.validate(hint)
        hint = copy.deepcopy(HINT); hint['capsule_pin']['path'] = hint['capsule_pin']['path'].replace('.v5.json', '.v4.json')
        with self.assertRaises(ValueError): API.validate(hint)

    def test_original_wire_hash_rejects_added_bytes(self):
        with self.assertRaises(ValueError): API.reconstruct(HINT, WIRE+b' ', CHECK)

    def changed(self, change):
        data = BOUNDED.decode_compact(WIRE.decode('ascii'), CHECK); change(data)
        raw = BOUNDED.encode_compact(data, CHECK).encode('ascii'); hint = copy.deepcopy(HINT)
        hint['capsule_pin'].update(bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())
        return hint, raw

    def mutated_row(self, index):
        def change(data): data['bindings'][index][0][2] = '0'*64
        hint, wire = self.changed(change)
        with self.assertRaises(ValueError): API.reconstruct(hint, wire, CHECK)

    def test_prior68_constructor_rejects_wire_tamper_after_rehash(self): self.mutated_row(0)
    def test_prior_legacy_constructor_rejects_wire_tamper_after_rehash(self): self.mutated_row(71)
    def test_prior154_constructor_rejects_wire_tamper_after_rehash(self): self.mutated_row(72)
    def test_each_new149_constructor_rejects_wire_tamper_after_rehash(self):
        self.mutated_row(73); self.mutated_row(74)

    def test_first_descriptor_and_product_promotion_are_denied(self):
        hint = copy.deepcopy(HINT); hint['first_descriptor']['semantic_original_pin']['sha256'] = '0'*64
        with self.assertRaises(ValueError): API.reconstruct(hint, WIRE, CHECK)
        hint = copy.deepcopy(HINT); hint[MODULE.FIELD]['current_product_or_GO_qualified'] = True
        with self.assertRaises(ValueError): API.validate(hint)

    def test_wire_and_bootstrap_remain_under_original16KiB(self):
        self.assertLessEqual(len(WIRE), 16384); self.assertLessEqual(HINT['capsule_pin']['bytes'], 16384)
        self.assertEqual(HINT['capsule_pin']['path'], MODULE.CAPSULE)
        self.assertLessEqual(len(MODULE.json.dumps(HINT, ensure_ascii=True, indent=2).encode('ascii'))+1, 16384)

    def test_reconstruction_has_no_data_JSON_opens_or_default_module_mutation(self):
        self.assertEqual(OBSERVED['data_file_opens'], 0); self.assertFalse(API.original_default_modules_mutated)

    def test_complete_previous3242_scope_not_just_fresh408_subset(self):
        self.assertEqual(len(BASIS), CODE['semantic_inputs']); self.assertEqual(len(BASIS), 3242)
        self.assertEqual(BASIS_BYTES, CODE['physical_bytes'])
        for r in HINT[MODULE.FIELD]['records']: self.assertEqual(BASIS[r['original']['path']], r['original'])

    def test_fresh_Source_policy_and_actual_preparation_reader_remain_connected(self):
        self.assertTrue(SOURCE.state.ready)
        self.assertIs(type(SOURCE.state.policy), SOURCE.state.alias.VerifiedPolicy)
        self.assertEqual(SOURCE.state.policy.evidence(), HINT['closed_prebody_source_declaration'])
        stats = READER.source_snapshot_diagnostics(); self.assertGreater(stats['source_requests'], 0)
        self.assertEqual(stats['source_requests'], stats['fresh_no_follow_stat_attempts'])
        self.assertFalse(stats['stat_result_cached_or_reused_between_source_requests'])
        workspace = CHUNK.summary(READER)
        self.assertEqual(workspace['workspace_allocations'], 1); self.assertEqual(workspace['leases'], workspace['lease_returns'])
        self.assertFalse(workspace['active_lease']); self.assertFalse(workspace['file_bytes_or_hash_or_JSON_cache'])

    def test_missing_duplicate_and_reordered_rows_fail_after_transport_rehash(self):
        def missing(data): data['bindings'].pop()
        def duplicate(data): data['bindings'][-1] = copy.deepcopy(data['bindings'][-2])
        def reordered(data): data['bindings'][-2:] = data['bindings'][-2:][::-1]
        for change in (missing, duplicate, reordered):
            hint, wire = self.changed(change)
            with self.assertRaises(ValueError): API.reconstruct(hint, wire, CHECK)


if __name__ == '__main__': unittest.main()
