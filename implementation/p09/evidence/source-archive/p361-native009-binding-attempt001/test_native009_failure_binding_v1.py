import copy
import hashlib
import unittest

M=MODULE=ROWS=PRIOR=PIN=CHECK=PROOF=REQUIRED=CARRIER=NATIVE=None


def construct(): return MODULE.Binding(ROWS,PIN,next_case=165)


class Tests(unittest.TestCase):
    def setUp(self): CHECK()
    def tearDown(self): CHECK()
    def test_complete161_then_raw162_are_both_retained(self):
        before=dict(PROOF.state); value=construct()
        self.assertEqual(value.descriptors(),ROWS)
        self.assertEqual(PROOF.state['prior_constructor_calls'],before['prior_constructor_calls']+1)
        self.assertEqual(PROOF.state['new_constructor_calls'],before['new_constructor_calls']+1)
    def test_prior_descriptors_are_not_changed_or_omitted(self):
        self.assertEqual(ROWS[:161],PRIOR); self.assertEqual(len(ROWS),162)
        self.assertEqual(ROWS[-1]['semantic_original_pin'],M.ORIGINAL); self.assertEqual(ROWS[-1]['physical_envelope_pin'],M.PHYSICAL)
    def test_all_other_methods_and_projection_identity_survive(self):
        self.assertTrue(all(vars(MODULE.Binding).get(n) is f for n,f in PROOF.methods.items()))
        self.assertTrue(all(vars(MODULE.source.Projection).get(n) is f for n,f in PROOF.projections.items()))
    def test_missing_reordered_duplicated_and_tampered_rows_fail_closed(self):
        changed=copy.deepcopy(ROWS); changed[-1]['physical_envelope_pin']['bytes']+=1
        for rows in (ROWS[:-1],list(reversed(ROWS)),ROWS[:-1]+[ROWS[0]],changed):
            with self.assertRaises(ValueError): MODULE.Binding(rows,PIN,next_case=165)
        construct()
    def test_exact_context_is_typed165(self):
        for case in (True,164,166):
            with self.assertRaises(ValueError): MODULE.Binding(ROWS,PIN,next_case=case)
        construct()
    def test_generic_metadata_current_or_unknown_runtime_cannot_replace_failure9(self):
        for name in ('tools/p09/source.py','implementation/p09/evidence/p09-361-case165-preflight.v1.json',
                'implementation/p09/evidence/p09-361-case165-current-runtime-run010.v1.json'):
            with self.assertRaises(ValueError): MODULE.source.descriptor(dict(M.ORIGINAL,path=name),M.PHYSICAL,next_case=165)
    def test_declared_semantic_scope_and_input_count_are_preserved(self):
        value=construct(); projection,_=value.project(REQUIRED,CHECK)
        self.assertEqual(dict(projection.semantic_pins),REQUIRED)
        self.assertEqual(len(projection.physical_pins),len(REQUIRED))
        self.assertNotIn(M.ORIGINAL['path'],projection.physical_pins)
        self.assertEqual(projection.physical_pins[M.PHYSICAL['path']],M.PHYSICAL)
    def test_original_or_physical_hash_substitution_is_rejected(self):
        for old,new in ((dict(M.ORIGINAL,sha256='0'*64),M.PHYSICAL),(M.ORIGINAL,dict(M.PHYSICAL,sha256='0'*64))):
            with self.assertRaises(ValueError): MODULE.source.descriptor(old,new,next_case=165)
    def test_actual_new_carrier_restores_the_entire_original_failure(self):
        construct(); raw=MODULE.source.codec.decode(CARRIER,CHECK)
        self.assertEqual(len(raw),M.ORIGINAL['bytes']); self.assertEqual(hashlib.sha256(raw).hexdigest(),M.ORIGINAL['sha256'])
        with self.assertRaises(ValueError): MODULE.source.codec.decode(CARRIER+b' ',CHECK)
    def test_true_execution_is_not_promoted_to_current_acceptance_or_replay(self):
        value=construct(); projection,_=value.project(REQUIRED,CHECK); row=value.representation(projection)
        role=row['native009_post_body_shared720_failure_provenance']
        self.assertTrue(role['actual_failed_product_child_executed']); self.assertFalse(role['original_failure_promoted'])
        self.assertFalse(role['current_product_or_GO_qualified']); self.assertFalse(role['product_replay_authorized'])
        self.assertFalse(role['original_failed_Native_qualified'])
    def test_existing_history_provenance_is_unchanged(self):
        value=construct(); projection,_=value.project(REQUIRED,CHECK); row=value.representation(projection)
        self.assertEqual(row['legacy_history_physical_evidence_provenance'],MODULE.legacy_history_catalog)
        self.assertEqual(NATIVE['state'],'STOPPED_NOT_ACCEPTED')
    def test_original_mapping_key_identity_is_still_enforced(self):
        value=construct(); bad=copy.deepcopy(REQUIRED); name=next(iter(bad)); bad['wrong-key']=bad.pop(name)
        with self.assertRaises(ValueError): value.semantic_union(bad,CHECK)


if __name__=='__main__': unittest.main()
