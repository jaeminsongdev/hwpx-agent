from types import SimpleNamespace as NS
import unittest

MODULE=RAW=ROW=None


def carrier():return dict(path=MODULE.destination(1),bytes=3,sha256='a'*64)


class Tests(unittest.TestCase):
    def test_exact_original_and_worker_writer_failure(self):
        MODULE.exact_original(MODULE.ORIGINAL,RAW)
        flags=MODULE.failure(ROW)
        self.assertTrue(flags['worker_created']);self.assertTrue(flags['writer_authorized'])
        self.assertFalse(flags['product_complete']);self.assertIsNone(flags['actual_product_child_executed'])

    def test_other_source_exe_or_current_receipt_pin_and_bytes_rejected(self):
        for path in ('tools/p09/source.py','target/product.exe','implementation/p09/evidence/p09-361-case165-current-runtime-run009.v1.json'):
            with self.assertRaises(ValueError):MODULE.exact_original(dict(MODULE.ORIGINAL,path=path),RAW)
        for raw in (RAW[:-1],RAW+b' ',b'changed'):
            with self.assertRaises(ValueError):MODULE.exact_original(MODULE.ORIGINAL,raw)

    def test_no_pass_prebody_or_boolean_integer_relabelling(self):
        for key,value in (('state','PASS'),('worker_created',False),('writer_authorized',False),('product_complete',True),
            ('cleanup_confirmed',False),('owned_tree_empty',False),('P09_gate','CLOSED'),('worker_created',1),('stop_reason','PREBODY')):
            with self.assertRaises(ValueError):MODULE.failure(dict(ROW,**{key:value}))

    def test_unknown_product_execution_not_false_or_true(self):
        for key in ('actual_product_child_executed','product_body_observed'):
            for value in (False,True,0,1):
                with self.assertRaises(ValueError):MODULE.failure(dict(ROW,**{key:value}))
        with self.assertRaises(ValueError):MODULE.failure(dict(ROW,passed_test_names=['invented_pass']))

    def test_finite_explicit_generation_and_physical_path(self):
        self.assertNotEqual(MODULE.destination(1),MODULE.ORIGINAL['path'])
        for value in (0,9,True,'1'):
            with self.assertRaises(ValueError):MODULE.destination(value)
        for pin in (dict(carrier(),path='other.json'),dict(carrier(),bytes=True),dict(carrier(),sha256='X'*64)):
            with self.assertRaises(ValueError):MODULE.physical_pin(pin)

    def test_two_calls_preserve_physical_buffer_not_logical_bytes(self):
        pin=carrier();calls=[];counts=[]
        class Reader:
            def _read(self,name,parse=False):calls.append((name,parse));return pin,bytearray(b'abc')
        bound=MODULE.reader_type(Reader,pin,NS(run=lambda op:op(lambda:None)),NS(decode=lambda raw,check:RAW),counts)()
        self.assertEqual(bound._read(pin['path']),(pin,None))
        self.assertEqual(bound._read(pin['path'],True),(pin,bytearray(b'abc')))
        self.assertEqual(calls,[(pin['path'],True)]*2);self.assertEqual(counts,[pin,pin])

    def test_physical_tamper_rejected_before_decoder(self):
        pin=carrier()
        class Reader:
            def _read(self,name,parse=False):return dict(pin,sha256='0'*64),b'abc'
        def denied(op):raise AssertionError('decoder must not run')
        bound=MODULE.reader_type(Reader,pin,NS(run=denied),None,[])()
        with self.assertRaises(ValueError):bound._read(pin['path'])

    def test_bad_decoded_original_never_counted_as_complete(self):
        pin=carrier();counts=[]
        class Reader:
            def _read(self,name,parse=False):return pin,b'abc'
        bound=MODULE.reader_type(Reader,pin,NS(run=lambda op:op(lambda:None)),NS(decode=lambda raw,check:b'bad'),counts)()
        with self.assertRaises(ValueError):bound._read(pin['path'])
        self.assertEqual(counts,[])

    def test_whole_prior72_reader_is_delegated_without_decoding_changes(self):
        calls=[];pin=carrier()
        class Reader:
            def _read(self,name,parse=False):calls.append((name,parse));return dict(path=name),None
        bound=MODULE.reader_type(Reader,pin,None,None,[])()
        self.assertEqual(bound._read('prior72'),(dict(path='prior72'),None));self.assertEqual(calls,[('prior72',False)])

    def test_only_failed_cleaned_same_generation_publication_is_reusable(self):
        record=dict(original=MODULE.ORIGINAL,physical=carrier(),source_role=MODULE.ROLE,
            original_failure_promoted=False,actual_failed_product_child_executed=None)
        row=dict(state='FAILED_LEGACY154_FULL73_PHYSICAL_NOT_ADOPTED',generation=1,attempt=1,cleanup_confirmed=True,
            accepted_count_delta=0,GO_authorized=False,product_or_Native_executed=False,original_overwritten_or_deleted=False,
            full73_binding_worker_or_Native_qualified=False,record=record)
        self.assertEqual(MODULE.reusable(row,1,2),record)
        for key,value in (('state','PASS'),('cleanup_confirmed',False),('generation',2),('attempt',2),('GO_authorized',True)):
            with self.assertRaises(ValueError):MODULE.reusable(dict(row,**{key:value}),1,2)
