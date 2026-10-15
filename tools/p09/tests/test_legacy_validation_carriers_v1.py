import json
import unittest
from types import SimpleNamespace as NS

MODULE=None
RAW=None


class Tests(unittest.TestCase):
    def test_reuse_only_failed_cleaned_same_generation_two_exact_records(self):
        row=dict(state='FAILED_LEGACY2_FULL72_PHYSICAL_NOT_ADOPTED',attempt=1,generation=1,cleanup_confirmed=True,
            product_or_Native_executed=False,GO_authorized=False,accepted_count_delta=0,original_overwritten_or_deleted=False,
            prior70_mapping_or_descriptor_policy_changed=False,full72_binding_worker_or_Native_scope_qualified=False,automatic_retry=False,
            records=[dict(key=r['key'],original=r['original'],physical=dict(path=MODULE.destination(r['key'],1),bytes=1,sha256='a'*64),
                source_role='historical_validation_worker_and_writer_started_duration_stop_not_accepted',original_failure_promoted=False,
                product_child_execution_asserted=False) for r in MODULE.RECORDS])
        self.assertEqual(MODULE.reusable_publication(row,1,2),row['records'])
        for key,value in (('cleanup_confirmed',False),('state','PASS'),('generation',2),('attempt',2),('GO_authorized',True)):
            with self.assertRaises(ValueError):MODULE.reusable_publication(dict(row,**{key:value}),1,2)
        with self.assertRaises(ValueError):MODULE.reusable_publication(dict(row,records=row['records'][:1]),1,2)

    def pairs(self):return [dict(key=r['key'],original=r['original'],physical=dict(path=r['key'],bytes=3,sha256='a'*64)) for r in MODULE.RECORDS]

    def test_exact_first_raw_and_original_failure(self):
        r=MODULE.RECORDS[0];MODULE.exact_original(r['key'],r['original'],RAW);MODULE.failed_state(r['key'],json.loads(RAW))

    def test_only_two_exact_receipts_not_source_exe_or_current_candidate(self):
        for key in ('tools/p09/source.py','current-runtime-run009','p159',True):
            with self.assertRaises(ValueError):MODULE.record(key)

    def test_original_bytes_and_pin_substitution_rejected(self):
        r=MODULE.RECORDS[0]
        for raw in (RAW[:-1],RAW+b' ',b'wrong'):
            with self.assertRaises(ValueError):MODULE.exact_original(r['key'],r['original'],raw)
        with self.assertRaises(ValueError):MODULE.exact_original(r['key'],dict(r['original'],sha256='0'*64),RAW)

    def test_failed_worker_writer_not_promoted_or_relabelled_prebody(self):
        row=json.loads(RAW);key=MODULE.RECORDS[0]['key']
        for field,value in (('state','PASS'),('product_complete',True),('P09_gate','CLOSED'),('worker_created',False),
            ('writer_authorized',False),('native_or_SQL_run',True),('job_assigned',False),('cleanup_confirmed',False),
            ('stop_reason','PREBODY_STOP'),('worker_created',1)):
            with self.assertRaises(ValueError):MODULE.failed_state(key,dict(row,**{field:value}))

    def test_separate_finite_destinations(self):
        names=[MODULE.destination(r['key'],1) for r in MODULE.RECORDS];self.assertEqual(len(set(names)),2)
        for r in MODULE.RECORDS:self.assertNotEqual(MODULE.destination(r['key'],1),r['original']['path'])
        for value in (0,9,True,'1'):
            with self.assertRaises(ValueError):MODULE.destination(MODULE.RECORDS[0]['key'],value)

    def test_two_actual_calls_return_physical_not_logical_bytes(self):
        pairs=self.pairs();pin=pairs[0]['physical'];calls=[];counts={}
        class Reader:
            def _read(self,name,parse=False):calls.append((name,parse));return pin,bytearray(b'abc') if parse else None
        reader=MODULE.reader_type(Reader,pairs,NS(run=lambda op:op(lambda:None)),NS(decode=lambda raw,check:RAW),counts)()
        self.assertEqual(reader._read(pin['path']),(pin,None));self.assertEqual(reader._read(pin['path'],True),(pin,bytearray(b'abc')))
        self.assertEqual(calls,[(pin['path'],True),(pin['path'],True)]);self.assertEqual(counts,{pin['path']:2})

    def test_physical_tamper_rejected_before_decoder(self):
        pairs=self.pairs()
        class Reader:
            def _read(self,name,parse=False):return dict(pairs[0]['physical'],sha256='0'*64),b'abc'
        def denied(op):raise AssertionError('decoder must not run')
        reader=MODULE.reader_type(Reader,pairs,NS(run=denied),None,{})()
        with self.assertRaises(ValueError):reader._read(pairs[0]['physical']['path'])

    def test_decode_failure_not_counted_as_completed(self):
        pairs=self.pairs();counts={}
        class Reader:
            def _read(self,name,parse=False):return pairs[0]['physical'],b'abc'
        reader=MODULE.reader_type(Reader,pairs,NS(run=lambda op:op(lambda:None)),NS(decode=lambda raw,check:b'wrong'),counts)()
        with self.assertRaises(ValueError):reader._read(pairs[0]['physical']['path'])
        self.assertEqual(counts,{})

    def test_prior_reader_and_duplicate_or_changed_table_controls(self):
        pairs=self.pairs()
        class Reader:
            def _read(self,name,parse=False):return dict(path=name),None
        reader=MODULE.reader_type(Reader,pairs,None,None,{})()
        self.assertEqual(reader._read('prior68'),(dict(path='prior68'),None))
        with self.assertRaises(ValueError):MODULE.reader_type(Reader,[pairs[0],pairs[0]],None,None,{})
