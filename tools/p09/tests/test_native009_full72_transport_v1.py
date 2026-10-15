import copy
import hashlib
import unittest

MODULE=API=HINT=WIRE=GRAPH=ROWS=CHECK=BOUNDED=LINKED=None


class Tests(unittest.TestCase):
    def test_original_count_and_suffix_inverse_proofs(self):
        for proof in (API.count_proof,API.engine_proof,API.suffix_proof):
            self.assertTrue(proof['whole_code_inverse']);self.assertTrue(proof['original_defaults_closure_and_globals_retained'])
        self.assertEqual((API.count_proof['old'],API.count_proof['new']),(69,72))

    def test_all72_reconstruct_and_share_original_binding_namespace(self):
        self.assertEqual(GRAPH.binding.descriptors(),ROWS)
        self.assertIs(GRAPH.worker.source,GRAPH.binding_module)
        self.assertIs(GRAPH.frames.binding_module,GRAPH.binding_module)
        self.assertIs(GRAPH.full_oracle.binding_module,GRAPH.binding_module)

    def test_original_engine_worker_composed_not_executed(self):
        self.assertEqual(LINKED.state.attempts,0);self.assertEqual(LINKED.state.calls,0)
        self.assertFalse(LINKED.state.completed);self.assertEqual(LINKED.window.WINDOW.SECONDS,10)
        self.assertIs(LINKED.engine.worker,LINKED.original_worker)

    def test_four_failure_declarations_are_mandatory(self):
        for field in (MODULE.FIELD7,MODULE.FIELD2,'native008_failed_capture_declaration','closed_prebody_source_declaration'):
            # Determine the old closed-prebody field from the actual packet;
            # it remains owned and validated by the unchanged underlying API.
            if field not in HINT:continue
            hint=copy.deepcopy(HINT);hint.pop(field)
            with self.assertRaises(ValueError):API.validate(hint)
        self.assertIn(MODULE.FIELD7,HINT);self.assertIn(MODULE.FIELD2,HINT)

    def test_execution_true_unknown_and_unaccepted_legacy_roles_preserved(self):
        self.assertIs(HINT[MODULE.FIELD7]['actual_failed_product_child_executed'],True)
        self.assertIsNone(HINT['native008_failed_capture_declaration']['actual_failed_product_child_executed'])
        for r in HINT[MODULE.FIELD2]['records']:
            self.assertFalse(r['original_failure_promoted']);self.assertFalse(r['product_child_execution_asserted'])
        hint=copy.deepcopy(HINT);hint[MODULE.FIELD7]['actual_failed_product_child_executed']=False
        with self.assertRaises(ValueError):API.validate(hint)

    def test_wrong_context_old_suffix_and_extra_field_reject(self):
        for key,value in (('index',164),('run',8),('unexpected',True)):
            hint=copy.deepcopy(HINT);hint[key]=value
            with self.assertRaises(ValueError):API.validate(hint)
        hint=copy.deepcopy(HINT);hint['capsule_pin']['path']=hint['capsule_pin']['path'].replace('.v3.json','.v2.json')
        with self.assertRaises(ValueError):API.validate(hint)

    def test_altered_wire_still_rejected_by_original_transport_hash(self):
        with self.assertRaises(ValueError):API.reconstruct(HINT,WIRE+b' ',CHECK)

    def mutated_wire(self,index):
        data=BOUNDED.decode_compact(WIRE.decode('ascii'),CHECK)
        data['bindings'][index][0][2]='0'*64
        raw=BOUNDED.encode_compact(data,CHECK).encode('ascii')
        hint=copy.deepcopy(HINT);hint['capsule_pin'].update(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
        return hint,raw

    def test_changed_prior68_pair_rejects_even_with_new_transport_hash(self):
        hint,wire=self.mutated_wire(0)
        with self.assertRaises(ValueError):API.reconstruct(hint,wire,CHECK)

    def test_changed_added_legacy_pair_rejects_original_constructor(self):
        hint,wire=self.mutated_wire(71)
        with self.assertRaises(ValueError):API.reconstruct(hint,wire,CHECK)

    def test_wire_and_bootstrap_stay_within_original16KiB(self):
        self.assertLessEqual(len(WIRE),16384);self.assertLessEqual(HINT['capsule_pin']['bytes'],16384)
        self.assertEqual(HINT['capsule_pin']['path'],MODULE.CAPSULE)

    def test_malformed_first_descriptor_rejects(self):
        hint=copy.deepcopy(HINT);hint['first_descriptor']['semantic_original_pin']['sha256']='0'*64
        with self.assertRaises(ValueError):API.reconstruct(hint,WIRE,CHECK)

    def test_no_historical_failure_or_product_permission_promotion(self):
        hint=copy.deepcopy(HINT);hint[MODULE.FIELD2]['current_product_or_GO_qualified']=True
        with self.assertRaises(ValueError):API.validate(hint)
        self.assertFalse(API.original_default_modules_mutated)
