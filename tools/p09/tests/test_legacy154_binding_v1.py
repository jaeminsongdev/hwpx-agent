import copy
import hashlib
import unittest

MODULE=BINDING=ROWS=PIN=SCOPE=CHECK=CARRIER=METHODS=PROJECTION=PRIOR=XZ=None


class Tests(unittest.TestCase):
    def bound(self):return BINDING.Binding(copy.deepcopy(ROWS),PIN,next_case=165)
    def required(self):return SCOPE.pins([r['semantic_original_pin'] for r in ROWS]+[PIN])

    def test_nonconstructor_and_all_Projection_methods_retained(self):
        self.assertTrue(all(vars(BINDING.Binding).get(n) is f for n,f in METHODS.items()))
        self.assertTrue(all(vars(BINDING.source.Projection).get(n) is f for n,f in PROJECTION.items()))

    def test_all73_projection_and_extra_source_retained(self):
        b=self.bound();rows=self.required();extra=dict(path=MODULE.SELF,bytes=1,sha256='a'*64);rows[extra['path']]=extra
        p,_=b.project(rows,CHECK);self.assertEqual(b.descriptors(),ROWS)
        self.assertEqual(len(p.semantic_pins),len(p.physical_pins));self.assertEqual(dict(p.semantic_pins[extra['path']]),extra)
        self.assertNotIn(MODULE.ORIGINAL['path'],p.physical_pins)
        self.assertEqual(dict(p.physical_pins[MODULE.PHYSICAL['path']]),MODULE.PHYSICAL)

    def test_unknown_duration_failure_not_pass_or_prebody_and_old_roles_survive(self):
        b=self.bound();p,_=b.project(self.required(),CHECK);r=b.representation(p)
        self.assertEqual(r['legacy154_validation_failure_provenance'],MODULE.ROLE)
        self.assertIsNone(r['legacy154_validation_failure_provenance']['actual_failed_product_child_executed'])
        self.assertFalse(r['legacy154_validation_failure_provenance']['original_failure_promoted'])
        self.assertIs(r['same_case_failed165_run007_provenance']['actual_failed_product_child_executed'],True)
        self.assertIsNone(r['same_case_failed165_run008_provenance']['actual_failed_product_child_executed'])
        self.assertEqual(len(r['historical_validation_failures_provenance']['records']),2)

    def test_actual_new_codec_bytes_hash_and_original_guard_first(self):
        self.bound();raw=BINDING.source.codec.decode(CARRIER,CHECK)
        self.assertEqual((len(raw),hashlib.sha256(raw).hexdigest()),(MODULE.ORIGINAL['bytes'],MODULE.ORIGINAL['sha256']))
        def stop():raise ValueError('ORIGINAL_STOP')
        with self.assertRaisesRegex(ValueError,'ORIGINAL_STOP'):BINDING.source.codec.decode(CARRIER,stop)

    def test_missing_duplicate_prior_or_new_tamper_rejected(self):
        for kind in ('missing','duplicate','prior','new'):
            rows=copy.deepcopy(ROWS)
            if kind=='missing':rows.pop()
            elif kind=='duplicate':rows[0]=copy.deepcopy(rows[1])
            elif kind=='prior':rows[0]['physical_envelope_pin']['sha256']='0'*64
            else:rows[-1]['semantic_original_pin']['sha256']='0'*64
            with self.assertRaises(ValueError):BINDING.Binding(rows,PIN,next_case=165)

    def test_wrong_case_missing_original_or_manifest_rejected(self):
        with self.assertRaises(ValueError):BINDING.Binding(ROWS,PIN,next_case=164)
        b=self.bound();rows=self.required();rows.pop(MODULE.ORIGINAL['path'])
        with self.assertRaises(ValueError):b.project(rows,CHECK)
        rows=self.required();rows[PIN['path']]=dict(PIN,sha256='0'*64)
        with self.assertRaises(ValueError):b.project(rows,CHECK)

    def test_exact_alias_reconciles_but_changed_physical_hash_rejects(self):
        b=self.bound();rows=self.required();rows[MODULE.PHYSICAL['path']]=MODULE.PHYSICAL
        semantic,_=b.semantic_union(rows,CHECK);self.assertEqual(semantic[MODULE.ORIGINAL['path']],MODULE.ORIGINAL)
        rows[MODULE.PHYSICAL['path']]=dict(MODULE.PHYSICAL,sha256='0'*64)
        with self.assertRaises(ValueError):b.semantic_union(rows,CHECK)

    def test_no_generic_metadata_source_exe_fixture_or_current_product_alias(self):
        self.bound()
        for path in ('tools/p09/source.py','target/product.exe','implementation/p09/fixtures/source.json',
            MODULE.PREFIX+'current-runtime-run009.v1.json','implementation/p09/evidence/other-legacy.json'):
            with self.assertRaises(ValueError):BINDING.source.descriptor(dict(MODULE.ORIGINAL,path=path),MODULE.PHYSICAL,next_case=165)

    def test_promoted_role_execution_assertion_other_run_and_reinstall_reject(self):
        for field,value in (('original_failure_promoted',True),('source_role','prebody_no_worker'),
            ('actual_failed_product_child_executed',False),('actual_failed_product_child_executed',True)):
            with self.assertRaises(ValueError):MODULE.install(BINDING,PRIOR,dict(MODULE.ROLE,**{field:value}),XZ,physical_run=9)
        with self.assertRaises(ValueError):MODULE.install(BINDING,PRIOR,MODULE.ROLE,XZ,physical_run=8)
        with self.assertRaises(ValueError):MODULE.install(BINDING,PRIOR,MODULE.ROLE,XZ,physical_run=9)

    def test_prior_descriptor_codec_and_unmapped_conflicts_retained(self):
        b=self.bound();r=PRIOR[0]
        self.assertEqual(BINDING.source.descriptor(r['semantic_original_pin'],r['physical_envelope_pin'],next_case=165),r)
        raw=BINDING.xz_original_codec.encode(b'old special',CHECK)
        self.assertEqual(BINDING.source.codec.decode(raw,CHECK),b'old special')
        rows=self.required();rows[MODULE.ORIGINAL['path']]=dict(MODULE.ORIGINAL,bytes=1)
        with self.assertRaises(ValueError):b.semantic_union(rows,CHECK)
