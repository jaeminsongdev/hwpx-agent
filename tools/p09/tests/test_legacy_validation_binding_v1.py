import copy
import hashlib
import unittest

MODULE=BINDING=ROWS=PIN=SCOPE=CHECK=CARRIERS=METHODS=PROJECTION=PRIOR=XZ=None


class Tests(unittest.TestCase):
    def bound(self):return BINDING.Binding(copy.deepcopy(ROWS),PIN,next_case=165)
    def required(self):return SCOPE.pins([r['semantic_original_pin'] for r in ROWS]+[PIN])

    def test_all_nonconstructor_and_projection_methods_retained(self):
        self.assertTrue(all(vars(BINDING.Binding).get(k) is v for k,v in METHODS.items()))
        self.assertTrue(all(vars(BINDING.source.Projection).get(k) is v for k,v in PROJECTION.items()))

    def test_whole72_projects_every_original_and_extra_source(self):
        b=self.bound();rows=self.required();extra=dict(path=MODULE.SELF,bytes=1,sha256='a'*64);rows[extra['path']]=extra
        p,_=b.project(rows,CHECK);self.assertEqual(b.descriptors(),ROWS)
        self.assertEqual(len(p.semantic_pins),len(p.physical_pins));self.assertEqual(dict(p.semantic_pins[extra['path']]),extra)
        for r in MODULE.RECORDS:
            self.assertEqual(dict(p.physical_pins[r['physical']['path']]),r['physical']);self.assertNotIn(r['original']['path'],p.physical_pins)

    def test_two_actual_codecs_and_original_guard_first(self):
        self.bound()
        for r,encoded in zip(MODULE.RECORDS,CARRIERS):
            raw=BINDING.source.codec.decode(encoded,CHECK)
            self.assertEqual((len(raw),hashlib.sha256(raw).hexdigest()),(r['original']['bytes'],r['original']['sha256']))
        def stop():raise ValueError('ORIGINAL_STOP')
        with self.assertRaisesRegex(ValueError,'ORIGINAL_STOP'):BINDING.source.codec.decode(CARRIERS[0],stop)

    def test_both_aliases_reconcile_and_changed_pin_rejects(self):
        b=self.bound();rows=self.required()
        for r in MODULE.RECORDS:rows[r['physical']['path']]=r['physical']
        semantic,_=b.semantic_union(rows,CHECK)
        for r in MODULE.RECORDS:self.assertEqual(semantic[r['original']['path']],r['original'])
        r=MODULE.RECORDS[0];rows[r['physical']['path']]=dict(r['physical'],sha256='0'*64)
        with self.assertRaises(ValueError):b.semantic_union(rows,CHECK)

    def test_legacy_failed_roles_and_native007_008_roles_are_separate(self):
        b=self.bound();p,_=b.project(self.required(),CHECK);row=b.representation(p)
        self.assertEqual(row['historical_validation_failures_provenance'],MODULE.ROLE)
        self.assertIs(row['same_case_failed165_run007_provenance']['actual_failed_product_child_executed'],True)
        self.assertIsNone(row['same_case_failed165_run008_provenance']['actual_failed_product_child_executed'])
        for r in row['historical_validation_failures_provenance']['records']:
            self.assertFalse(r['original_failure_promoted']);self.assertFalse(r['product_child_execution_asserted'])
            self.assertIn('worker_and_writer_started',r['source_role'])

    def test_missing_duplicate_changed_old_or_new_rows_reject(self):
        for kind in ('missing','duplicate','old','new'):
            rows=copy.deepcopy(ROWS)
            if kind=='missing':rows.pop()
            elif kind=='duplicate':rows[0]=copy.deepcopy(rows[1])
            elif kind=='old':rows[0]['physical_envelope_pin']['sha256']='0'*64
            else:rows[-1]['semantic_original_pin']['sha256']='0'*64
            with self.assertRaises(ValueError):BINDING.Binding(rows,PIN,next_case=165)

    def test_wrong_case_missing_original_and_changed_manifest_reject(self):
        with self.assertRaises(ValueError):BINDING.Binding(ROWS,PIN,next_case=164)
        b=self.bound();rows=self.required();rows.pop(MODULE.RECORDS[0]['original']['path'])
        with self.assertRaises(ValueError):b.project(rows,CHECK)
        rows=self.required();rows[PIN['path']]=dict(PIN,sha256='0'*64)
        with self.assertRaises(ValueError):b.project(rows,CHECK)

    def test_other_legacy_receipt_source_or_current_product_not_whitelisted(self):
        self.bound();r=MODULE.RECORDS[0]
        for path in ('tools/p09/source.py','target/product.exe','implementation/p09/fixtures/source.json',
            MODULE.PREFIX+'current-runtime-run009.v1.json','implementation/p09/evidence/other-legacy-run.json'):
            with self.assertRaises(ValueError):BINDING.source.descriptor(dict(r['original'],path=path),r['physical'],next_case=165)

    def test_promoted_or_prebody_role_replay_and_reinstallation_reject(self):
        for field,value in (('original_failure_promoted',True),('source_role','prebody_no_worker'),('product_child_execution_asserted',True)):
            role=copy.deepcopy(MODULE.ROLE);role['records'][0][field]=value
            with self.assertRaises(ValueError):MODULE.install(BINDING,PRIOR,role,XZ,physical_run=9)
        with self.assertRaises(ValueError):MODULE.install(BINDING,PRIOR,MODULE.ROLE,XZ,physical_run=8)
        with self.assertRaises(ValueError):MODULE.install(BINDING,PRIOR,MODULE.ROLE,XZ,physical_run=9)

    def test_fixed70_table_and_old_codec_still_enforced(self):
        self.bound();r=PRIOR[0]
        self.assertEqual(BINDING.source.descriptor(r['semantic_original_pin'],r['physical_envelope_pin'],next_case=165),r)
        raw=BINDING.xz_original_codec.encode(b'old special',CHECK)
        self.assertEqual(BINDING.source.codec.decode(raw,CHECK),b'old special')
        with self.assertRaises(ValueError):MODULE.install(BINDING,PRIOR[:-1],MODULE.ROLE,XZ,physical_run=9)

    def test_unmapped_conflicts_are_not_silently_rebased(self):
        b=self.bound();rows=self.required();r=MODULE.RECORDS[1]
        rows[r['original']['path']]=dict(r['original'],bytes=1)
        with self.assertRaises(ValueError):b.semantic_union(rows,CHECK)
