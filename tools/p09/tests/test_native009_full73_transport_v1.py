import copy
import hashlib
import unittest

MODULE=API=HINT=WIRE=GRAPH=ROWS=CHECK=BOUNDED=LINKED=OBSERVED=BASIS=PREVIOUS_CODE=BASIS_BYTES=READER=ORIGINAL_READER=None


class Tests(unittest.TestCase):
    def test_all73_and_shared_original_private_graph(self):
        self.assertEqual(GRAPH.binding.descriptors(),ROWS)
        self.assertIs(GRAPH.worker.source,GRAPH.binding_module)
        self.assertIs(GRAPH.frames.binding_module,GRAPH.binding_module)
        self.assertIs(GRAPH.full_oracle.binding_module,GRAPH.binding_module)

    def test_exact_count_and_suffix_slot_inverses(self):
        for proof in (API.inner_count_proof,API.outer_count_proof,API.engine_proof):
            self.assertEqual((proof['old'],proof['new']),(72,73));self.assertTrue(proof['whole_code_inverse'])
            self.assertTrue(proof['original_defaults_closure_and_globals_retained'])
        self.assertEqual((API.suffix_proof['old'],API.suffix_proof['new']),('.compact.v3.json','.compact.v4.json'))
        self.assertTrue(API.suffix_proof['whole_code_inverse'])

    def test_one_named_closure_dependency_not_whole_body_replacement(self):
        self.assertEqual(API.closure_proof['dependency'],'reconstruction');self.assertTrue(API.closure_proof['entire_closure_inverse'])
        self.assertEqual(API.original_outer.__code__.co_filename,API.revised_outer.__code__.co_filename)
        self.assertEqual(API.original_inner.__code__.co_filename,API.revised_inner.__code__.co_filename)
        slots=list(API.original_outer.__code__.co_freevars);i=slots.index('reconstruction')
        self.assertIs(API.original_outer.__closure__[i].cell_contents,API.original_inner)
        self.assertIs(API.revised_outer.__closure__[i].cell_contents,API.revised_inner)
        for n in range(len(slots)):
            if n!=i:self.assertIs(API.original_outer.__closure__[n],API.revised_outer.__closure__[n])

    def test_original_engine_worker_composed_once_not_executed(self):
        self.assertEqual((LINKED.state.attempts,LINKED.state.calls),(0,0));self.assertFalse(LINKED.state.completed)
        self.assertEqual(LINKED.window.WINDOW.SECONDS,10);self.assertIs(LINKED.engine.worker,LINKED.original_worker)

    def test_all_existing_and_new_failure_declarations_are_mandatory(self):
        for field in (MODULE.FIELD,'native007_executed_failure_declaration','legacy_validation_failure_declarations',
            'native008_failed_capture_declaration','closed_prebody_source_declaration'):
            self.assertIn(field,HINT);hint=copy.deepcopy(HINT);hint.pop(field)
            with self.assertRaises(ValueError):API.validate(hint)

    def test_execution_true_unknown_and_legacy_failure_provenance_preserved(self):
        self.assertIsNone(HINT[MODULE.FIELD]['actual_failed_product_child_executed'])
        self.assertFalse(HINT[MODULE.FIELD]['original_failure_promoted'])
        self.assertIs(HINT['native007_executed_failure_declaration']['actual_failed_product_child_executed'],True)
        self.assertIsNone(HINT['native008_failed_capture_declaration']['actual_failed_product_child_executed'])
        for r in HINT['legacy_validation_failure_declarations']['records']:self.assertFalse(r['original_failure_promoted'])
        for value in (False,True):
            hint=copy.deepcopy(HINT);hint[MODULE.FIELD]['actual_failed_product_child_executed']=value
            with self.assertRaises(ValueError):API.validate(hint)

    def test_wrong_context_extra_field_and_previous_suffix_reject(self):
        for key,value in (('index',164),('run',8),('unexpected',True)):
            hint=copy.deepcopy(HINT);hint[key]=value
            with self.assertRaises(ValueError):API.validate(hint)
        hint=copy.deepcopy(HINT);hint['capsule_pin']['path']=hint['capsule_pin']['path'].replace('.v4.json','.v3.json')
        with self.assertRaises(ValueError):API.validate(hint)

    def test_original_transport_hash_rejects_changed_wire(self):
        with self.assertRaises(ValueError):API.reconstruct(HINT,WIRE+b' ',CHECK)

    def mutated(self,index):
        data=BOUNDED.decode_compact(WIRE.decode('ascii'),CHECK);data['bindings'][index][0][2]='0'*64
        raw=BOUNDED.encode_compact(data,CHECK).encode('ascii');hint=copy.deepcopy(HINT)
        hint['capsule_pin'].update(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest());return hint,raw

    def test_original_fixed_prior68_rejects_tamper_after_transport_rehash(self):
        hint,wire=self.mutated(0)
        with self.assertRaises(ValueError):API.reconstruct(hint,wire,CHECK)

    def test_prior_legacy_row_constructor_still_rejects_tamper(self):
        hint,wire=self.mutated(71)
        with self.assertRaises(ValueError):API.reconstruct(hint,wire,CHECK)

    def test_new_p154_row_original_constructor_rejects_tamper(self):
        hint,wire=self.mutated(72)
        with self.assertRaises(ValueError):API.reconstruct(hint,wire,CHECK)

    def test_first_descriptor_and_product_promotion_reject(self):
        hint=copy.deepcopy(HINT);hint['first_descriptor']['semantic_original_pin']['sha256']='0'*64
        with self.assertRaises(ValueError):API.reconstruct(hint,WIRE,CHECK)
        hint=copy.deepcopy(HINT);hint[MODULE.FIELD]['current_product_or_GO_qualified']=True
        with self.assertRaises(ValueError):API.validate(hint)

    def test_wire_bootstrap_within_original16KiB(self):
        self.assertLessEqual(len(WIRE),16384);self.assertLessEqual(HINT['capsule_pin']['bytes'],16384)
        self.assertEqual(HINT['capsule_pin']['path'],MODULE.CAPSULE)

    def test_no_data_json_io_or_default_namespace_mutation(self):
        self.assertEqual(OBSERVED['data_file_opens'],0);self.assertFalse(API.original_default_modules_mutated)

    def test_full_previous_scope_not_just_the_freshly_read_subset(self):
        self.assertEqual(len(BASIS),PREVIOUS_CODE['semantic_inputs']);self.assertEqual(len(BASIS),3207)
        self.assertEqual(BASIS_BYTES,PREVIOUS_CODE['physical_bytes'])
        expected={
            'implementation/p09/evidence/p09-361-case165-native009-full72-construction003.v1.json':82460,
            'implementation/p09/evidence/p09-361-case165-native009-production-worker-launch001.v1.json':73756}
        for name,size in expected.items():self.assertEqual(BASIS[name]['bytes'],size)

    def test_fresh_one_stat_reader_preserves_original_reads_hashes_and_guards(self):
        self.assertIs(READER._read.__func__,ORIGINAL_READER._read)
        self.assertIs(READER.pin.__func__,ORIGINAL_READER.pin)
        self.assertIs(READER.fresh_pin.__func__,ORIGINAL_READER.fresh_pin)
        stats=READER.source_snapshot_diagnostics()
        self.assertGreater(stats['ordinary_windows_snapshot_decisions'],0)
        self.assertEqual(stats['source_requests'],stats['fresh_no_follow_stat_attempts'])
        self.assertFalse(stats['stat_result_cached_or_reused_between_source_requests'])
        self.assertFalse(stats['held_Native_path_guard_replaced'])
