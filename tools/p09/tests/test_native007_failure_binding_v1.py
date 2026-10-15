import copy
import hashlib
import unittest

MODULE=BINDING=ROWS=PIN=SCOPE=CHECK=CARRIER=METHODS=PROJECTION=PRIOR=XZ=None


class Tests(unittest.TestCase):
    def bound(self):return BINDING.Binding(copy.deepcopy(ROWS),PIN,next_case=165)
    def required(self):return SCOPE.pins([r['semantic_original_pin'] for r in ROWS]+[PIN])

    def test_original_nonconstructor_and_projection_functions_unchanged(self):
        self.assertTrue(all(vars(BINDING.Binding).get(k) is v for k,v in METHODS.items()))
        self.assertTrue(all(vars(BINDING.source.Projection).get(k) is v for k,v in PROJECTION.items()))

    def test_whole70_projection_preserves_every_semantic_input(self):
        bound=self.bound();required=self.required();extra=dict(path=MODULE.SELF,bytes=1,sha256='a'*64)
        required[extra['path']]=extra
        projection,_=bound.project(required,CHECK)
        self.assertEqual(bound.descriptors(),ROWS);self.assertEqual(dict(projection.semantic_pins[extra['path']]),extra)
        self.assertEqual(len(projection.semantic_pins),len(projection.physical_pins))
        self.assertEqual(dict(projection.physical_pins[MODULE.PHYSICAL['path']]),MODULE.PHYSICAL)
        self.assertNotIn(MODULE.ORIGINAL['path'],projection.physical_pins)

    def test_exact_alias_reconciles_and_changed_alias_rejects(self):
        bound=self.bound();required=self.required();required[MODULE.PHYSICAL['path']]=MODULE.PHYSICAL
        semantic,_=bound.semantic_union(required,CHECK);self.assertEqual(semantic[MODULE.ORIGINAL['path']],MODULE.ORIGINAL)
        required[MODULE.PHYSICAL['path']]=dict(MODULE.PHYSICAL,sha256='0'*64)
        with self.assertRaises(ValueError):bound.semantic_union(required,CHECK)

    def test_actual_decode_after_full_constructor_and_original_guard_first(self):
        self.bound();raw=BINDING.source.codec.decode(CARRIER,CHECK)
        self.assertEqual((len(raw),hashlib.sha256(raw).hexdigest()),(MODULE.ORIGINAL['bytes'],MODULE.ORIGINAL['sha256']))
        def stop():raise ValueError('ORIGINAL_STOP')
        with self.assertRaisesRegex(ValueError,'ORIGINAL_STOP'):BINDING.source.codec.decode(CARRIER,stop)

    def test_both_distinct_failure_roles_and_old_history_preserved(self):
        bound=self.bound();projection,_=bound.project(self.required(),CHECK);row=bound.representation(projection)
        self.assertEqual(row['same_case_failed165_run007_provenance'],MODULE.ROLE)
        self.assertIs(row['same_case_failed165_run007_provenance']['actual_failed_product_child_executed'],True)
        self.assertIsNone(row['same_case_failed165_run008_provenance']['actual_failed_product_child_executed'])
        self.assertFalse(row['same_case_failed165_run007_provenance']['original_failure_promoted'])
        self.assertIn('historical_predecessor_provenance',row)

    def test_missing_duplicate_changed_original_and_wrong_case_reject(self):
        for kind in ('missing','duplicate','old','new'):
            rows=copy.deepcopy(ROWS)
            if kind=='missing':rows.pop()
            elif kind=='duplicate':rows[0]=copy.deepcopy(rows[1])
            elif kind=='old':rows[0]['physical_envelope_pin']['sha256']='0'*64
            else:rows[-1]['semantic_original_pin']['sha256']='0'*64
            with self.assertRaises(ValueError):BINDING.Binding(rows,PIN,next_case=165)
        with self.assertRaises(ValueError):BINDING.Binding(ROWS,PIN,next_case=164)

    def test_no_run9_current_product_descriptor_or_false_execution(self):
        self.bound()
        for key,value in (('actual_failed_product_child_executed',False),('actual_failed_product_child_executed',None),
            ('original_failure_promoted',True),('current_case',164)):
            with self.assertRaises(ValueError):MODULE.install(BINDING,PRIOR,dict(MODULE.ROLE,**{key:value}),XZ,physical_run=9)
        with self.assertRaises(ValueError):MODULE.install(BINDING,PRIOR,MODULE.ROLE,XZ,physical_run=8)
        with self.assertRaises(ValueError):BINDING.source.descriptor(dict(MODULE.ORIGINAL,path=MODULE.ORIGINAL['path'].replace('run007','run009')),MODULE.PHYSICAL,next_case=165)

    def test_original_prior_table_old_codec_and_reinstallation_controls(self):
        self.bound();first=PRIOR[0]
        self.assertEqual(BINDING.source.descriptor(first['semantic_original_pin'],first['physical_envelope_pin'],next_case=165),first)
        raw=BINDING.xz_original_codec.encode(b'original old format',CHECK)
        self.assertEqual(BINDING.source.codec.decode(raw,CHECK),b'original old format')
        with self.assertRaises(ValueError):MODULE.install(BINDING,PRIOR[:-1],MODULE.ROLE,XZ,physical_run=9)
        with self.assertRaises(ValueError):MODULE.install(BINDING,PRIOR,MODULE.ROLE,XZ,physical_run=9)

    def test_missing_original_or_changed_manifest_rejects(self):
        bound=self.bound();rows=self.required();rows.pop(MODULE.ORIGINAL['path'])
        with self.assertRaises(ValueError):bound.project(rows,CHECK)
        rows=self.required();rows[PIN['path']]=dict(PIN,sha256='0'*64)
        with self.assertRaises(ValueError):bound.project(rows,CHECK)
