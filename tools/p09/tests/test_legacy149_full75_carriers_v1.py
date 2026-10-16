from types import SimpleNamespace as NS
import unittest

MODULE=RAW=ROWS=None
PRIOR_SPECS=PRIOR72=EXACT=None
CHECKPOINT=lambda:None


def records():
    return [dict(key=spec['key'],original=spec['original'],physical=dict(path=MODULE.destination(spec['key'],1),bytes=3,sha256='a'*64),
        source_role=MODULE.ROLE,original_stop_reason=spec['stop_reason'],original_failure_promoted=False,
        actual_failed_product_child_executed=None) for spec in MODULE.RECORDS]


class Tests(unittest.TestCase):
    def setUp(self):CHECKPOINT()
    def tearDown(self):CHECKPOINT()

    def test_both_exact_original_pins_and_bytes(self):
        for spec in MODULE.RECORDS:MODULE.exact_original(spec['key'],spec['original'],RAW[spec['key']])

    def test_swapped_or_other_source_current_product_pin_rejected(self):
        spec=MODULE.RECORDS[0];raw=RAW[spec['key']]
        for path in ('tools/p09/source.py','target/product.exe','implementation/p09/evidence/p09-361-case165-current-runtime-run009.v1.json'):
            with self.assertRaises(ValueError):MODULE.exact_original(spec['key'],dict(spec['original'],path=path),raw)
        with self.assertRaises(ValueError):MODULE.exact_original('run01',MODULE.RECORDS[1]['original'],RAW['run02'])

    def test_mutated_or_truncated_raw_never_accepted(self):
        spec=MODULE.RECORDS[0];raw=RAW['run01']
        for changed in (raw[:-1],raw+b' ',b'changed'):
            with self.assertRaises(ValueError):MODULE.exact_original('run01',spec['original'],changed)

    def test_distinct_failure_reasons_preserved(self):
        flags=[MODULE.failure(spec['key'],ROWS[spec['key']]) for spec in MODULE.RECORDS]
        self.assertEqual([r['stop_reason'] for r in flags],['OWNED_RUNNER_FAILURE','STOP_LOW_AVAILABLE_RAM'])
        for row in flags:self.assertTrue(row['writer_authorized']);self.assertFalse(row['product_complete'])
        with self.assertRaises(ValueError):MODULE.failure('run01',ROWS['run02'])

    def test_no_pass_prebody_or_boolean_integer_relabelling(self):
        for key,value in (('state','PASS'),('worker_created',False),('writer_authorized',False),('heavy_work_started',False),
            ('worker_created',1),('product_complete',True),('cleanup_confirmed',False),('owned_tree_empty',False),('P09_gate','CLOSED')):
            with self.assertRaises(ValueError):MODULE.failure('run01',dict(ROWS['run01'],**{key:value}))

    def test_unknown_execution_never_false_or_true(self):
        for key in ('actual_product_child_executed','product_body_observed'):
            for value in (False,True,0,1):
                with self.assertRaises(ValueError):MODULE.failure('run01',dict(ROWS['run01'],**{key:value}))

    def test_finite_identifiers_paths_and_exact_keys(self):
        for value in (0,9,True,'1'):
            with self.assertRaises(ValueError):MODULE.destination('run01',value)
        with self.assertRaises(ValueError):MODULE.destination('other',1)
        pin=records()[0]['physical']
        for changed in (dict(pin,path=MODULE.destination('run02',1)),dict(pin,bytes=True),dict(pin,sha256='X'*64)):
            with self.assertRaises(ValueError):MODULE.physical_pin('run01',changed)

    def test_two_fresh_reads_keep_physical_bytes_and_count_each(self):
        selected=records();pin=selected[0]['physical'];calls=[];counts={}
        class Reader:
            def _read(self,name,parse=False):calls.append((name,parse));return pin,bytearray(b'abc')
        candidate=MODULE.reader_type(Reader,selected,NS(run=lambda op:op(lambda:None)),NS(decode=lambda raw,check:RAW['run01']),counts)()
        self.assertEqual(candidate._read(pin['path']),(pin,None))
        self.assertEqual(candidate._read(pin['path'],True),(pin,bytearray(b'abc')))
        self.assertEqual(calls,[(pin['path'],True)]*2);self.assertEqual(counts,{pin['path']:2})

    def test_physical_tamper_rejected_before_decoder(self):
        selected=records();pin=selected[0]['physical']
        class Reader:
            def _read(self,name,parse=False):return dict(pin,sha256='0'*64),b'abc'
        def denied(op):raise AssertionError('decoder must not run')
        candidate=MODULE.reader_type(Reader,selected,NS(run=denied),None,{})()
        with self.assertRaises(ValueError):candidate._read(pin['path'])

    def test_bad_restored_original_never_counted(self):
        selected=records();pin=selected[0]['physical'];counts={}
        class Reader:
            def _read(self,name,parse=False):return pin,b'abc'
        candidate=MODULE.reader_type(Reader,selected,NS(run=lambda op:op(lambda:None)),NS(decode=lambda raw,check:b'bad'),counts)()
        with self.assertRaises(ValueError):candidate._read(pin['path'])
        self.assertEqual(counts,{})

    def test_prior73_is_delegated_without_replacement(self):
        calls=[]
        class Reader:
            def _read(self,name,parse=False):calls.append((name,parse));return dict(path=name),None
        candidate=MODULE.reader_type(Reader,records(),None,None,{})()
        self.assertEqual(candidate._read('prior73'),(dict(path='prior73'),None));self.assertEqual(calls,[('prior73',False)])

    def test_prior_legacy_keys_and_fixed_originals_retained(self):
        pairs=MODULE.prior_legacy_pairs(PRIOR_SPECS,PRIOR72,EXACT)
        self.assertEqual([r['key'] for r in pairs],[r['key'] for r in PRIOR_SPECS])
        self.assertEqual([r['physical'] for r in pairs],[r['physical_envelope_pin'] for r in PRIOR72[70:72]])
        changed=[dict(r) for r in PRIOR72]
        changed[70]['semantic_original_pin']=dict(changed[70]['semantic_original_pin'],path='target/current-product.exe')
        with self.assertRaises(ValueError):MODULE.prior_legacy_pairs(PRIOR_SPECS,changed,EXACT)

    def test_only_cleaned_failed_same_generation_publication_reusable(self):
        selected=records();row=dict(state='FAILED_LEGACY149_FULL75_PHYSICAL_NOT_ADOPTED',generation=1,attempt=1,
            cleanup_confirmed=True,accepted_count_delta=0,GO_authorized=False,product_or_Native_executed=False,
            original_overwritten_or_deleted=False,full75_binding_worker_or_Native_qualified=False,records=selected)
        self.assertEqual(MODULE.reusable(row,1,2),selected)
        for key,value in (('state','PASS'),('generation',2),('attempt',2),('cleanup_confirmed',False),('GO_authorized',True)):
            with self.assertRaises(ValueError):MODULE.reusable(dict(row,**{key:value}),1,2)
