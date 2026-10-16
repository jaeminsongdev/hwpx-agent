"""Fixed161 contracts over the real private75 factory; no engine or product."""
import copy
import hashlib
import unittest

M=CATALOG=MODULE=BOUND=PIN=REQUIRED=CHECK=PROOF=FACTORY=XZ=CARRIERS=NATIVE=None


def construct(): return MODULE.Binding(CATALOG.rows(),PIN,next_case=165)


class Tests(unittest.TestCase):
    def setUp(self): CHECK()
    def tearDown(self): CHECK()
    def test_exact161_is_old75_repacked_seven_plus_86_only(self):
        rows=CATALOG.rows(); prior=CATALOG.prior()
        self.assertEqual(len(rows),161); self.assertEqual(len(prior),75)
        self.assertEqual([r['semantic_original_pin'] for r in rows[:75]],[r['semantic_original_pin'] for r in prior])
        self.assertEqual(sum(x!=y for x,y in zip(rows,prior)),7)
        self.assertEqual(len({r['semantic_original_pin']['path'] for r in rows}),161)
    def test_entire_old75_runs_before_whole_raw161(self):
        before=dict(PROOF.state); result=construct()
        self.assertEqual(result.descriptors(),CATALOG.rows())
        self.assertEqual(PROOF.state['prior_constructor_calls'],before['prior_constructor_calls']+1)
        self.assertEqual(PROOF.state['new_constructor_calls'],before['new_constructor_calls']+1)
        self.assertTrue(PROOF.state['ready']); self.assertFalse(PROOF.state['validating_prior'])
    def test_all_other_binding_and_projection_methods_are_identical(self):
        self.assertTrue(all(vars(MODULE.Binding).get(n) is f for n,f in PROOF.methods.items()))
        self.assertTrue(all(vars(MODULE.source.Projection).get(n) is f for n,f in PROOF.projections.items()))
    def test_fixed_rows_cannot_be_missing_reordered_duplicated_or_changed(self):
        rows=CATALOG.rows()
        bad=[rows[:-1],list(reversed(rows)),rows[:-1]+[rows[0]]]
        changed=copy.deepcopy(rows); changed[-1]['physical_envelope_pin']['bytes']+=1; bad.append(changed)
        for value in bad:
            with self.assertRaises(ValueError): MODULE.Binding(value,PIN,next_case=165)
        construct()
    def test_context_is_exact_typed165(self):
        for value in (True,164,166):
            with self.assertRaises(ValueError): MODULE.Binding(CATALOG.rows(),PIN,next_case=value)
        construct()
    def test_generic_metadata_and_source_are_still_rejected(self):
        physical=CATALOG.rows()[-1]['physical_envelope_pin']
        for path in ('tools/p09/source.py','implementation/p09/evidence/p09-361-case165-preflight.v1.json',
                'implementation/p09/evidence/p09-181-not_in_fixed_catalog.v1.json'):
            old=dict(CATALOG.rows()[-1]['semantic_original_pin'],path=path)
            with self.assertRaises(ValueError): MODULE.source.descriptor(old,physical,next_case=165)
    def test_original_source_or_physical_pin_tampering_is_rejected(self):
        row=CATALOG.rows()[-1]
        for old,new in ((dict(row['semantic_original_pin'],sha256='0'*64),row['physical_envelope_pin']),
                (row['semantic_original_pin'],dict(row['physical_envelope_pin'],bytes=row['physical_envelope_pin']['bytes']+1))):
            with self.assertRaises(ValueError): MODULE.source.descriptor(old,new,next_case=165)
    def test_whole_semantic_scope_and_unmapped_inputs_survive(self):
        bound=construct(); projection,_=bound.project(REQUIRED,CHECK)
        self.assertEqual(dict(projection.semantic_pins),REQUIRED)
        self.assertEqual(len(projection.semantic_pins),len(projection.physical_pins))
        self.assertEqual(projection.semantic_pins[NATIVE['compiled_test_executable_pin']['path']],NATIVE['compiled_test_executable_pin'])
    def test_all_seven_old_physical_aliases_reconcile_only_exactly(self):
        bound=construct(); extra=copy.deepcopy(REQUIRED)
        for r in CATALOG.declaration()['old_seven_descriptors']:
            p=r['physical_envelope_pin']; extra[p['path']]=dict(p)
        value,_=bound.semantic_union(extra,CHECK)
        self.assertEqual(value,REQUIRED)
    def test_wrong_old_physical_hash_is_not_silently_rebased(self):
        bound=construct(); extra=copy.deepcopy(REQUIRED); p=CATALOG.declaration()['old_seven_descriptors'][0]['physical_envelope_pin']
        extra[p['path']]=dict(p,sha256='0'*64)
        with self.assertRaises(ValueError): bound.semantic_union(extra,CHECK)
    def test_original_mapping_key_identity_is_preserved(self):
        bound=construct(); extra=copy.deepcopy(REQUIRED); name=next(iter(extra)); extra['wrong-key']=extra.pop(name)
        with self.assertRaises(ValueError): bound.semantic_union(extra,CHECK)
    def test_worker_declaration_cannot_claim_parent_admission(self):
        worker=M.from_transport(CATALOG.rows(),CATALOG.declaration())
        self.assertFalse(worker.parent_source_admitted)
        with self.assertRaises(AttributeError): worker.parent_source_admitted=True
        with self.assertRaises(ValueError) as caught: M.install(MODULE,worker,XZ,mode='parent')
        self.assertEqual(caught.exception.args,('LEGACY_HISTORY_BINDING_PARENT_SOURCE_ADMISSION_REQUIRED',))
    def test_worker_reconstructs_same_fixed_binding_without_product_authority(self):
        worker=M.from_transport(CATALOG.rows(),CATALOG.declaration()); other=FACTORY()
        proof=M.install(other,worker,XZ,mode='worker'); result=other.Binding(worker.rows(),PIN,next_case=165)
        self.assertEqual(result.descriptors(),CATALOG.rows()); self.assertFalse(proof.product_execution_authorized)
        self.assertFalse(proof.parent_source_admitted)
    def test_transport_role_context_or_authority_tampering_is_rejected(self):
        for delta in (dict(product_execution_authorized=True),dict(current_case=166),dict(original_missing_fields_not_defaulted=False),dict(catalog_sha256='0'*64)):
            with self.assertRaises(ValueError): M.from_transport(CATALOG.rows(),dict(CATALOG.declaration(),**delta))
    def test_catalog_returns_copies_not_mutable_bound_tables(self):
        rows=CATALOG.rows(); declaration=CATALOG.declaration()
        rows[0]['physical_envelope_pin']['bytes']+=1; declaration['product_execution_authorized']=True
        self.assertEqual(M.fingerprint(CATALOG.rows()),M.COMPLETE_SHA)
        self.assertEqual(M.fingerprint(CATALOG.declaration()),M.DECLARATION_SHA)
    def test_actual_new_history_and_repacked_carriers_restore_original_hashes(self):
        construct()
        for row,raw in CARRIERS:
            decoded=MODULE.source.codec.decode(raw,CHECK); expected=row['semantic_original_pin']
            self.assertEqual(len(decoded),expected['bytes']); self.assertEqual(hashlib.sha256(decoded).hexdigest(),expected['sha256'])
    def test_actual_tampered_new_carrier_never_decodes_as_valid_original(self):
        construct()
        for row,raw in CARRIERS:
            with self.assertRaises(ValueError): MODULE.source.codec.decode(raw+b' ',CHECK)
    def test_original_provenance_not_overwritten_or_promoted(self):
        bound=construct(); projection,_=bound.project(REQUIRED,CHECK); representation=bound.representation(projection)
        prior=NATIVE['source_input_representation']
        structural={'manifest_pin','semantic_source_freeze','physical_source_freeze','descriptors'}
        for name,value in prior.items():
            if name not in structural: self.assertEqual(representation[name],value,name)
        self.assertEqual(representation['legacy_history_physical_evidence_provenance'],CATALOG.declaration())
        self.assertFalse(representation['legacy_history_physical_evidence_provenance']['product_execution_authorized'])


if __name__=='__main__': unittest.main()
