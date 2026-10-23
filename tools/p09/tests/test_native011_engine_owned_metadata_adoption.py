import hashlib
import io
from pathlib import Path
import time
import unittest
import audit_evidence_io as original
import owned_source_read_pressure as pressure
import owned_input_read_pressure as query
import reusable_audit_chunk_v1 as chunk
import native011_exact_read_budget as exact
import native011_metadata_tail_candidate as tail
import native011_engine_owned_metadata_adoption as m

RAW=(Path(__file__).resolve().parents[3]/exact.ORIGINAL['path']).read_bytes()


def fixture():
    data=b'{"a":1}';state=dict(data=data,reads=[],opens=0,paths=0,check_error=None)
    def check():
        if state['check_error']:raise state['check_error']
    class Stream(io.BytesIO):
        def readinto(self,buffer):state['reads'].append(len(buffer));return super().readinto(buffer)
    class Source:
        def open(self,mode):state['opens']+=1;return Stream(state['data'])
    class Build(pressure.prior.WeightedReader):
        def __init__(self,*args,**kwargs):
            super().__init__(*args,**kwargs);self.open_pacer=query.QueryPacer(self.checkpoint)
        def _source(self,name):state['paths']+=1;return Source()
        def _read(self,name,parse=False):self.open_pacer.reserve();return super()._read(name,parse=parse)
    pin=dict(path='physical.json',bytes=len(data),sha256=hashlib.sha256(data).hexdigest())
    Selected,_=tail.reader_type(Build,{pin['path']:pin},exact,pressure,original,chunk,RAW,pacer_policy='metadata_weighted')
    Product,proof=m.reader_type(Selected,exact,pressure)
    return Product('.',check),state,pin,Selected,proof


class Tests(unittest.TestCase):
    def test_original_assignment_retains_owned_rates_all_reads_eof_and_closing(self):
        reader,state,pin,_,proof=fixture();incoming=pressure.OwnedPacer();before=dict(vars(incoming))
        reader.pacer=incoming;self.assertEqual(vars(incoming),before)
        self.assertIn('pacer',vars(reader));self.assertIs(reader.pacer.clock,time.perf_counter)
        reader.pacer.select('file.exe');self.assertEqual(reader.pacer.rate,1048576)
        reader.pacer.select(pin['path']);self.assertEqual(reader.pacer.rate,2097152)
        self.assertEqual(reader.json(pin['path']),{'a':1});reader.finish()
        row=m.summary(reader);self.assertTrue(row['original_engine_owned_assignment_adopted'])
        self.assertEqual(row['semantic_final_fresh_hashes'],1);self.assertEqual(row['physical_bytes_read'],14)
        self.assertEqual(state['reads'],[7,1,7,1]);self.assertEqual(state['paths'],2)
        self.assertEqual(reader.open_pacer.requests,2);self.assertEqual(reader.pacer.reservations,4)
        self.assertFalse(proof['installed_in_product_entry']);self.assertFalse(row['actual_Native_or_product_qualified'])

    def test_unassigned_read_is_refused_and_cannot_be_recovered_by_late_assignment(self):
        reader,state,pin,_,_=fixture()
        with self.assertRaisesRegex(ValueError,'ASSIGNMENT_REQUIRED'):reader.fresh_pin(pin['path'])
        self.assertEqual(state['opens'],0)
        with self.assertRaises(ValueError):reader.pacer=pressure.OwnedPacer()
        self.assertTrue(m.summary(reader)['failed'])

    def test_repeated_or_used_assignment_never_resets_budget(self):
        reader,state,pin,_,_=fixture();reader.pacer=pressure.OwnedPacer();old=reader.pacer
        with self.assertRaisesRegex(ValueError,'ONE_ORIGINAL_ENGINE_ASSIGNMENT'):reader.pacer=pressure.OwnedPacer()
        self.assertIs(reader.pacer,old);self.assertTrue(m.summary(reader)['failed'])
        for kind in ('tokens','bytes','clock','type'):
            reader,state,pin,_,_=fixture();incoming=pressure.OwnedPacer()
            if kind=='tokens':incoming.tokens=0
            if kind=='bytes':incoming.bytes_paced=1
            if kind=='clock':incoming.clock=time.perf_counter
            if kind=='type':incoming=pressure.prior.WeightedPacer()
            with self.assertRaises(ValueError):reader.pacer=incoming
            self.assertEqual(state['opens'],0)

    def test_original_resource_error_priority_and_failure_identity_preserved(self):
        reader,state,pin,_,_=fixture();error=ValueError('ORIGINAL_CPU_RAM_STOP');state['check_error']=error
        with self.assertRaises(ValueError) as caught:reader.json(pin['path'])
        self.assertIs(caught.exception,error);self.assertEqual(state['opens'],0)

    def test_closing_changed_bytes_and_unknown_input_keep_original_refusals(self):
        reader,state,pin,_,_=fixture();reader.pacer=pressure.OwnedPacer();reader.pin(pin['path']);state['data']=b'{"a":2}'
        with self.assertRaisesRegex(ValueError,'input_changed_during_audit'):reader.finish()
        self.assertEqual(reader.final_fresh_hashes,0)
        with self.assertRaises(ValueError):reader.pacer=pressure.OwnedPacer()
        reader,state,pin,_,_=fixture();reader.pacer=pressure.OwnedPacer()
        with self.assertRaisesRegex(ValueError,'DECLARED_INPUT_ONLY'):reader.fresh_pin('unknown')
        self.assertEqual(state['opens'],0)

    def test_default_selected_reader_and_original_constructor_assignments_unchanged(self):
        reader,state,pin,Selected,proof=fixture();other=Selected('.',lambda:None)
        self.assertEqual(other.pacer.rate,4194304);self.assertNotIn(m.ATTRIBUTE,vars(other))
        self.assertEqual(m.summary(reader)['assignment_attempts'],0)
        self.assertFalse(proof['default_classes_or_engine_body_modified'])
        self.assertFalse(proof['original_Native_guard_deadline_or_shared_budget_changed'])
