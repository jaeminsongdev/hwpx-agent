import copy
import hashlib
import unittest

M=API=HINT=WIRE=ROWS=CHECK=GRAPH=PROOF=OBSERVED=None


class Tests(unittest.TestCase):
    def setUp(self): CHECK()
    def tearDown(self): CHECK()
    def test_source_pinned_history_matches_the_full_fixed_declaration(self):
        self.assertEqual(API.history.fingerprint(API.data),API.history.DECLARATION_SHA)
        self.assertEqual(HINT[M.MODULE_FIELD],M.DATA)
    def test_complete162_and_one_original_binding_namespace(self):
        self.assertEqual(GRAPH.binding.descriptors(),ROWS)
        for owner in (GRAPH.worker,GRAPH.frames,GRAPH.full_oracle):
            self.assertIs(owner.source if owner is GRAPH.worker else owner.binding_module,GRAPH.binding_module)
    def test_original75_stage_is_not_falsely_claimed_as_actual_old_transport(self):
        self.assertTrue(PROOF['constructor_packet_is_derived_not_external_transport'])
        self.assertTrue(PROOF['all_history161_and_failure162_constructors_completed'])
        self.assertGreaterEqual(API.state.constructor75_calls,1); self.assertGreaterEqual(API.state.actual162_decodes,1)
    def test_original_16k_bounds_and_explicit_source_module_not_historical_JSON(self):
        self.assertLessEqual(len(WIRE),16384); self.assertLessEqual(len(M.bootstrap_bytes(HINT)),16384)
        self.assertTrue(M.DATA['path'].endswith('.py'))
        self.assertNotIn('legacy_history_physical_evidence_provenance',HINT)
    def test_no_data_JSON_open_or_parent_permission_from_declaration(self):
        self.assertEqual(OBSERVED['JSON_file_opens'],0)
        self.assertFalse(API.catalog(ROWS).parent_source_admitted); self.assertFalse(API.state.history_parent_admission)
    def test_missing_each_new_role_field_is_denied(self):
        for key in (M.MODULE_FIELD,M.FAILURE_FIELD):
            hint=copy.deepcopy(HINT); hint.pop(key)
            with self.assertRaises(ValueError): API.validate(hint)
    def test_source_module_hash_or_path_cannot_be_substituted(self):
        for key,value in (('sha256','0'*64),('path','implementation/p09/evidence/old.json')):
            hint=copy.deepcopy(HINT); hint[M.MODULE_FIELD][key]=value
            with self.assertRaises(ValueError): API.validate(hint)
    def test_true_failed_product_execution_does_not_grant_current_GO(self):
        role=HINT[M.FAILURE_FIELD]; self.assertIs(role['actual_failed_product_child_executed'],True)
        for key in ('original_failure_promoted','original_failed_Native_qualified','current_product_or_GO_qualified','product_replay_authorized'):
            self.assertIs(role[key],False)
            hint=copy.deepcopy(HINT); hint[M.FAILURE_FIELD][key]=True
            with self.assertRaises(ValueError): API.validate(hint)
    def test_old_failure_roles_remain_mandatory(self):
        for key in ('closed_prebody_source_declaration','native008_failed_capture_declaration','native007_executed_failure_declaration',
                'legacy_validation_failure_declarations','legacy154_validation_failure_declaration','legacy149_validation_failure_declarations'):
            hint=copy.deepcopy(HINT); hint.pop(key)
            with self.assertRaises(ValueError): API.validate(hint)
    def test_wrong_context_unknown_field_and_old_suffix_are_denied(self):
        for key,value in (('index',True),('index',164),('run',8),('unexpected',True)):
            hint=copy.deepcopy(HINT); hint[key]=value
            with self.assertRaises(ValueError): API.validate(hint)
        hint=copy.deepcopy(HINT); hint['capsule_pin']['path']=hint['capsule_pin']['path'].replace('.v6.json','.v5.json')
        with self.assertRaises(ValueError): API.validate(hint)
    def test_actual_transport_hash_rejects_added_bytes(self):
        with self.assertRaises(ValueError): API.reconstruct(HINT,WIRE+b' ',CHECK)
    def changed(self,change):
        compact=API.binary.decode_compact(WIRE.decode('ascii'),CHECK); change(compact)
        wire=API.binary.encode_compact(compact,CHECK).encode('ascii'); hint=copy.deepcopy(HINT)
        hint['capsule_pin'].update(bytes=len(wire),sha256=hashlib.sha256(wire).hexdigest()); return hint,wire
    def test_missing_duplicated_or_reordered_rows_reject_after_valid_transport_hash(self):
        def missing(c): c['bindings'].pop()
        def duplicate(c): c['bindings'][-1]=copy.deepcopy(c['bindings'][-2])
        def reorder(c): c['bindings'][-2:]=c['bindings'][-2:][::-1]
        for change in (missing,duplicate,reorder):
            hint,wire=self.changed(change)
            with self.assertRaises(ValueError): API.reconstruct(hint,wire,CHECK)
    def test_changed_prior_history_and_new_failure_pin_reject_after_transport_rehash(self):
        for index in (0,74,75,160,161):
            def tamper(c): c['bindings'][index][0][2]='0'*64
            hint,wire=self.changed(tamper)
            with self.assertRaises(ValueError): API.reconstruct(hint,wire,CHECK)
    def test_actual_original_decoder_rejects_context_even_with_valid_transport_hash(self):
        def tamper(c): c['context'][2]=157
        hint,wire=self.changed(tamper)
        with self.assertRaises(ValueError): API.reconstruct(hint,wire,CHECK)
    def test_actual_current_manifest_is_checked_not_only_internal_constructor_manifest(self):
        def tamper(c): c['manifest'][2]='0'*64
        hint,wire=self.changed(tamper)
        with self.assertRaises(ValueError): API.reconstruct(hint,wire,CHECK)
    def test_original_suffix_code_inverse_and_worker_still_not_admitted(self):
        self.assertTrue(API.suffix_proof['whole_code_inverse'])
        self.assertEqual((API.suffix_proof['old'],API.suffix_proof['new']),('.compact.v5.json','.compact.v6.json'))
        self.assertFalse(API.actual_engine_or_product_permission_provided)


if __name__=='__main__': unittest.main()
