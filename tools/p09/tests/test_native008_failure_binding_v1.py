import copy
import unittest

MODULE=None
ADMITTED=None
FOUNDATION=None
XZ=None
SCOPE=None
CHECKPOINT=None
CARRIER=None


def installed():
    CHECKPOINT();module=FOUNDATION.factory()
    proof=MODULE.install(module,FOUNDATION.rows,ADMITTED,XZ,physical_run=9)
    row=dict(schema_version=module.source.SCHEMA,next_case=165,
        semantic_original_pin=dict(MODULE.ORIGINAL),physical_envelope_pin=dict(MODULE.PHYSICAL))
    return module,copy.deepcopy(FOUNDATION.rows)+[row],proof


class Tests(unittest.TestCase):
    def test_whole_original_constructor_and_nonconstructor_oracles_retained(self):
        CHECKPOINT();module=FOUNDATION.factory()
        methods={k:v for k,v in vars(module.Binding).items() if k not in ('__init__','representation')}
        projection=dict(vars(module.source.Projection));raw=module.xz_original_initialize
        MODULE.install(module,FOUNDATION.rows,ADMITTED,XZ,physical_run=9)
        self.assertTrue(all(vars(module.Binding)[k] is v for k,v in methods.items()))
        self.assertTrue(all(vars(module.source.Projection)[k] is v for k,v in projection.items()))
        self.assertIs(module.xz_original_initialize,raw)

    def test_complete69_real_binding_projects_original_and_physical_without_scope_loss(self):
        m,rows,proof=installed();bound=m.Binding(rows,FOUNDATION.manifest_pin,next_case=165)
        required=SCOPE.pins([r['semantic_original_pin'] for r in rows]+[FOUNDATION.manifest_pin])
        projection,_=bound.project(required,CHECKPOINT)
        self.assertEqual(bound.descriptors(),rows)
        self.assertEqual(len(projection.semantic_pins),len(projection.physical_pins))
        self.assertEqual(projection.physical_pins[MODULE.PHYSICAL['path']],MODULE.PHYSICAL)
        self.assertNotIn(MODULE.ORIGINAL['path'],projection.physical_pins)

    def test_exact_physical_alias_reconciles_but_arbitrary_alias_rejects(self):
        m,rows,_=installed();bound=m.Binding(rows,FOUNDATION.manifest_pin,next_case=165)
        required=SCOPE.pins([r['semantic_original_pin'] for r in rows]+[FOUNDATION.manifest_pin,MODULE.PHYSICAL])
        semantic,_=bound.semantic_union(required,CHECKPOINT)
        self.assertEqual(semantic[MODULE.ORIGINAL['path']],MODULE.ORIGINAL)
        required[MODULE.PHYSICAL['path']]=dict(MODULE.PHYSICAL,sha256='0'*64)
        with self.assertRaises(ValueError):bound.semantic_union(required,CHECKPOINT)

    def test_same_case_role_retains_unknown_execution_and_old_provenance(self):
        m,rows,_=installed();bound=m.Binding(rows,FOUNDATION.manifest_pin,next_case=165)
        required=SCOPE.pins([r['semantic_original_pin'] for r in rows]+[FOUNDATION.manifest_pin])
        projection,_=bound.project(required,CHECKPOINT);rep=bound.representation(projection)
        self.assertEqual(rep['same_case_failed165_run008_provenance'],ADMITTED)
        self.assertIsNone(rep['same_case_failed165_run008_provenance']['actual_failed_product_child_executed'])
        self.assertFalse(rep['same_case_failed165_run008_provenance']['original_failure_promoted'])
        self.assertIn('historical_predecessor_provenance',rep)

    def test_failure_codec_requires_complete_constructor_then_real_original_bytes(self):
        m,rows,_=installed()
        with self.assertRaises(ValueError):m.source.codec.decode(CARRIER,CHECKPOINT)
        m.Binding(rows,FOUNDATION.manifest_pin,next_case=165)
        restored=m.source.codec.decode(CARRIER,CHECKPOINT)
        import hashlib
        self.assertEqual(len(restored),MODULE.ORIGINAL['bytes'])
        self.assertEqual(hashlib.sha256(restored).hexdigest(),MODULE.ORIGINAL['sha256'])

    def test_missing_duplicate_or_changed_old_pair_never_constructs(self):
        for kind in ('missing','duplicate','old_pin'):
            m,rows,_=installed()
            if kind=='missing':rows.pop(0)
            elif kind=='duplicate':rows[0]=rows[1]
            else:rows[0]['physical_envelope_pin']['sha256']='0'*64
            with self.assertRaises(ValueError):m.Binding(rows,FOUNDATION.manifest_pin,next_case=165)

    def test_changed_failure_original_physical_or_current_product_rejected(self):
        m,_,_=installed()
        for old,new in ((dict(MODULE.ORIGINAL,sha256='0'*64),MODULE.PHYSICAL),
                        (MODULE.ORIGINAL,dict(MODULE.PHYSICAL,sha256='0'*64)),
                        (dict(MODULE.ORIGINAL,path=MODULE.ORIGINAL['path'].replace('run008','run009')),MODULE.PHYSICAL)):
            with self.assertRaises(ValueError):m.source.descriptor(old,new,next_case=165)

    def test_replay8_or_false_execution_claim_or_other_case_cannot_be_admitted(self):
        for change in ({'actual_failed_product_child_executed':False},{'current_case':164},{'original_failure_promoted':True}):
            m=FOUNDATION.factory()
            with self.assertRaises(ValueError):MODULE.install(m,FOUNDATION.rows,dict(ADMITTED,**change),XZ,physical_run=9)
        m=FOUNDATION.factory()
        with self.assertRaises(ValueError):MODULE.install(m,FOUNDATION.rows,ADMITTED,XZ,physical_run=8)

    def test_existing_table_fingerprint_and_reinstallation_rejected(self):
        m=FOUNDATION.factory();bad=copy.deepcopy(FOUNDATION.rows);bad.pop()
        with self.assertRaises(ValueError):MODULE.install(m,bad,ADMITTED,XZ,physical_run=9)
        MODULE.install(m,FOUNDATION.rows,ADMITTED,XZ,physical_run=9)
        with self.assertRaises(ValueError):MODULE.install(m,FOUNDATION.rows,ADMITTED,XZ,physical_run=9)

    def test_old_codec_and_ordinary_descriptor_still_work_and_guard_is_first(self):
        m,rows,_=installed();m.Binding(rows,FOUNDATION.manifest_pin,next_case=165)
        encoded=m.xz_original_codec.encode(b'old special',CHECKPOINT)
        self.assertEqual(m.source.codec.decode(encoded,CHECKPOINT),b'old special')
        first=rows[0];self.assertEqual(m.source.descriptor(first['semantic_original_pin'],first['physical_envelope_pin'],next_case=165),first)
        calls=[]
        def stop():calls.append(1);raise ValueError('ORIGINAL_STOP')
        with self.assertRaisesRegex(ValueError,'ORIGINAL_STOP'):m.source.codec.decode(CARRIER,stop)
        self.assertEqual(calls,[1])

    def test_wrong_case_and_mutated_manifest_reject_before_projection(self):
        m,rows,_=installed()
        with self.assertRaises(ValueError):m.Binding(rows,FOUNDATION.manifest_pin,next_case=164)
        bound=m.Binding(rows,FOUNDATION.manifest_pin,next_case=165)
        bad=dict(FOUNDATION.manifest_pin,sha256='0'*64)
        required=SCOPE.pins([r['semantic_original_pin'] for r in rows]+[bad])
        with self.assertRaises(ValueError):bound.project(required,CHECKPOINT)

    def test_input_admission_mutation_does_not_change_captured_provenance(self):
        CHECKPOINT();m=FOUNDATION.factory();admitted=copy.deepcopy(ADMITTED)
        MODULE.install(m,FOUNDATION.rows,admitted,XZ,physical_run=9)
        admitted['actual_failed_product_child_executed']=False
        self.assertEqual(m.native008_failure_alias,ADMITTED)
