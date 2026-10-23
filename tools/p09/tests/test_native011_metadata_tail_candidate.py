"""Uninstalled metadata-tail component; no Native or product execution."""
import hashlib
import io
import time
from pathlib import Path
from types import SimpleNamespace as NS
import unittest
import audit_evidence_io as original
import owned_source_read_pressure as pressure
import reusable_audit_chunk_v1 as chunk
import native011_exact_read_budget as exact
import native011_metadata_tail_candidate as candidate
import fresh_lossless_metadata_reader_v1 as lossless
import owned_input_read_pressure as open_policy
from test_native011_exact_read_budget import Clock

RAW=(Path(__file__).resolve().parents[3]/exact.ORIGINAL['path']).read_bytes()


def fixture(data=b'{"a":1}',declared=None):
    state=dict(data=data,open_wrappers=0,path_wrappers=0,checks=0,stream_opens=0,read_sizes=[],fail=False)
    def checkpoint():
        state['checks']+=1
        if state.get('stop'):raise ValueError('MODEL_RESOURCE_STOP')
    class Stream(io.BytesIO):
        def readinto(self,buffer):
            state['read_sizes'].append(len(buffer))
            if state['fail']:raise OSError('MODEL_IO_FAILURE')
            return super().readinto(buffer[:state.get('fragment',len(buffer))])
    class Source:
        def open(self,mode):
            state['stream_opens']+=1;return Stream(state['data'])
    class BuildReader(pressure.WeightedReader):
        def __init__(self,*args,**kwargs):
            super().__init__(*args,**kwargs)
            self.open_pacer=NS(reserve=lambda:state.__setitem__('open_wrappers',state['open_wrappers']+1))
        def _read(self,name,parse=False):
            self.open_pacer.reserve()
            return super()._read(name,parse=parse)
        def _source(self,name):
            state['path_wrappers']+=1
            return Source()
    pin=dict(path='fixture.json',bytes=len(data) if declared is None else declared,
        sha256=hashlib.sha256(data).hexdigest())
    Reader,proof=candidate.reader_type(BuildReader,{pin['path']:pin},exact,pressure,original,chunk,RAW)
    reader=Reader('.',checkpoint);clock=Clock()
    reader.pacer.clock=clock.now;reader.pacer.last=clock.now();reader.pacer.sleeper=clock.sleep
    return reader,state,pin,BuildReader,proof


class Tests(unittest.TestCase):
    def test_all_original_wrappers_execute_on_both_real_read_boundaries(self):
        reader,state,pin,base,proof=fixture()
        self.assertIs(type(reader)._read,base._read);self.assertIs(type(reader)._source,base._source)
        self.assertEqual(reader.json(pin['path']),{'a':1});reader.finish()
        self.assertEqual(reader.snapshots,{pin['path']:pin});self.assertEqual(reader.final_fresh_hashes,1)
        self.assertEqual((state['open_wrappers'],state['path_wrappers'],state['stream_opens']),(2,2,2))
        self.assertEqual(state['read_sizes'],[7,1,7,1]);self.assertEqual(reader.pacer.reservations,4)
        self.assertEqual(reader.bytes_read,14);self.assertTrue(proof['original_wrapper_MRO_order_and_method_identities_retained'])
        self.assertFalse(proof['metadata_factory_or_Native_or_product_connected'])

    def test_growth_short_read_and_closing_change_cannot_supply_credit(self):
        reader,state,pin,_,_=fixture();reader.pin(pin['path']);state['data']=b'{"a":2}'
        with self.assertRaisesRegex(ValueError,'input_changed_during_audit'):reader.finish()
        self.assertEqual(reader.final_fresh_hashes,0)
        reader,state,pin,_,_=fixture(declared=6)
        with self.assertRaisesRegex(ValueError,'FRESH_EXTRA_BYTE'):reader.pin(pin['path'])
        self.assertTrue(reader.pacer.failed);self.assertEqual(reader.snapshots,{})
        reader,state,pin,_,_=fixture();state['fragment']=2
        self.assertEqual(reader.fresh_pin(pin['path']),pin);self.assertEqual(reader.bytes_read,7)

    def test_original_io_and_resource_failures_preserved(self):
        reader,state,pin,_,_=fixture();state['fail']=True
        with self.assertRaisesRegex(OSError,'MODEL_IO_FAILURE'):reader.pin(pin['path'])
        self.assertTrue(reader.pacer.failed);state['fail']=False
        with self.assertRaises(ValueError):reader.fresh_pin(pin['path'])
        self.assertEqual(state['stream_opens'],1)
        reader,state,pin,_,_=fixture();state['stop']=True
        with self.assertRaisesRegex(ValueError,'MODEL_RESOURCE_STOP'):reader.pin(pin['path'])
        self.assertEqual(state['stream_opens'],0)

    def test_existing_lossless_semantic_wrapper_still_reads_and_decodes_fresh(self):
        reader,state,pin,_,_=fixture();semantic=dict(path='semantic.json',bytes=7,sha256=pin['sha256'])
        calls=[]
        def decode(name,actual,raw,check):calls.append(name);check();return raw
        projection=NS(semantic_pins={'semantic.json':semantic},physical_pins={'fixture.json':pin},next_case=165,decode_fresh=decode)
        rows=[dict(schema_version='fixture',semantic_original_pin=semantic,physical_envelope_pin=pin,next_case=165)]
        Routed=lossless.reader_type(type(reader),projection,rows);routed=Routed('.',reader.checkpoint)
        clock=Clock();routed.pacer.clock=clock.now;routed.pacer.last=clock.now();routed.pacer.sleeper=clock.sleep
        self.assertEqual(routed.json('semantic.json'),{'a':1});routed.finish()
        self.assertEqual(calls,['semantic.json','semantic.json']);self.assertEqual(routed.read_passes,2)
        self.assertEqual(routed.final_fresh_hashes,1);self.assertEqual(state['open_wrappers'],2)
        self.assertEqual(routed.lossless_metadata_completed,2)

    def test_parse_budget_invalid_json_unknown_path_original_source_drift_refused(self):
        reader,state,pin,_,_=fixture(b'not-json')
        with self.assertRaisesRegex(ValueError,'audit_json_invalid'):reader.json(pin['path'])
        reader,state,pin,_,_=fixture();reader.maximum_parse_bytes=2
        with self.assertRaisesRegex(ValueError,'audit_parse_budget_exceeded'):reader.json(pin['path'])
        reader,state,pin,base,_=fixture()
        with self.assertRaisesRegex(ValueError,'DECLARED_INPUT_ONLY'):reader.fresh_pin('unknown')
        self.assertEqual(state['stream_opens'],0)
        with self.assertRaises(ValueError):candidate.reader_type(base,{pin['path']:pin},exact,pressure,original,chunk,RAW+b'\n')

    def test_original_default_classes_and_other_instances_unchanged(self):
        saved=(pressure.WeightedReader._read,pressure.prior.WeightedReader._read,original.AuditEvidenceReader._read)
        reader,state,pin,base,_=fixture();untouched=base('.',lambda:None)
        self.assertIs(type(untouched),base);self.assertIs(type(untouched.pacer),pressure.OwnedPacer)
        self.assertFalse(hasattr(untouched,'_exact_input_sizes'))
        self.assertEqual(saved,(pressure.WeightedReader._read,pressure.prior.WeightedReader._read,original.AuditEvidenceReader._read))
        second=type(reader)('.',lambda:None)
        self.assertIsNot(reader.pacer,second.pacer);self.assertIsNot(reader._exact_input_sizes,second._exact_input_sizes)
        self.assertEqual(second.read_passes,0);self.assertEqual(second.snapshots,{})

    def test_no_faster_undeclared_or_preused_pacer_is_admitted(self):
        reader,state,pin,base,_=fixture()
        class Bad(base):
            def __init__(self,*args,**kwargs):
                super().__init__(*args,**kwargs);self.pacer=pressure.prior.WeightedPacer()
        Reader,_=candidate.reader_type(Bad,{pin['path']:pin},exact,pressure,original,chunk,RAW)
        with self.assertRaisesRegex(ValueError,'FRESH_ORIGINAL_OWNED'):Reader('.',lambda:None)
        class Used(base):
            def __init__(self,*args,**kwargs):
                super().__init__(*args,**kwargs);self.read_passes=1
        Reader,_=candidate.reader_type(Used,{pin['path']:pin},exact,pressure,original,chunk,RAW)
        with self.assertRaisesRegex(ValueError,'FRESH_ORIGINAL_OWNED'):Reader('.',lambda:None)

    def test_full_chunks_and_tail_keep_single_workspace_and_full_bytes(self):
        reader,state,pin,_,_=fixture(b'x'*(2*65536+17));reader.pin(pin['path']);reader.finish()
        self.assertEqual(state['read_sizes'],[65536,65536,17,1]*2)
        self.assertEqual(reader.bytes_read,2*pin['bytes']);self.assertEqual(reader.pacer.bytes_paced,reader.bytes_read)
        stats=chunk.summary(reader);self.assertEqual(stats['workspace_allocations'],1)
        self.assertEqual(stats['readinto_completed'],8);self.assertFalse(stats['active_lease'])

    def test_optional_precise_clocks_before_any_query_preserve_original_algorithms(self):
        _,state,pin,base,_=fixture()
        class RealQuery(base):
            def __init__(self,*args,**kwargs):
                super().__init__(*args,**kwargs)
                self.open_pacer=open_policy.QueryPacer(self.checkpoint)
        Reader,proof=candidate.reader_type(RealQuery,{pin['path']:pin},exact,pressure,original,chunk,RAW,
            precise=True,query_type=open_policy.QueryPacer)
        reader=Reader('.',lambda:None)
        self.assertIs(reader.pacer.clock,time.perf_counter);self.assertIs(reader.open_pacer.clock,time.perf_counter)
        self.assertIs(type(reader.open_pacer),open_policy.QueryPacer)
        self.assertIs(reader.open_pacer.sleep,time.sleep);self.assertIs(reader.pacer.sleeper,time.sleep)
        self.assertIs(reader.open_pacer.checkpoint,reader.checkpoint)
        self.assertEqual(reader.read_passes,0);self.assertEqual(reader.open_pacer.requests,0)
        self.assertTrue(proof['optional_precise_unused_clocks'])
        self.assertFalse(proof['active_deadline_or_used_counter_reset'])

    def test_used_or_substituted_query_clock_is_not_restarted(self):
        _,state,pin,base,_=fixture()
        for bad in ('used','clock','class'):
            class Bad(base):
                def __init__(self,*args,**kwargs):
                    super().__init__(*args,**kwargs)
                    self.open_pacer=open_policy.QueryPacer(self.checkpoint)
                    if bad=='used':self.open_pacer.requests=1
                    if bad=='clock':self.open_pacer.clock=time.perf_counter
                    if bad=='class':self.open_pacer=NS(requests=0,wait_seconds=0)
            Reader,_=candidate.reader_type(Bad,{pin['path']:pin},exact,pressure,original,chunk,RAW,
                precise=True,query_type=open_policy.QueryPacer)
            with self.assertRaisesRegex(ValueError,'EXACT_UNUSED'):Reader('.',lambda:None)
        with self.assertRaisesRegex(ValueError,'EXPLICIT_OPTIONAL'):
            candidate.reader_type(base,{pin['path']:pin},exact,pressure,original,chunk,RAW,precise=True)

    def test_existing_verified_workspace_leaf_keeps_all_open_and_path_wrappers(self):
        _,state,pin,base,_=fixture()
        Existing,_=chunk.reader_type(base,RAW)
        Reader,proof=candidate.reader_type(Existing,{pin['path']:pin},exact,pressure,original,chunk,RAW)
        reader=Reader('.',lambda:None);clock=Clock()
        reader.pacer.clock=clock.now;reader.pacer.last=clock.now();reader.pacer.sleeper=clock.sleep
        reader.pin(pin['path']);reader.finish()
        self.assertEqual((state['open_wrappers'],state['path_wrappers']),(2,2))
        self.assertEqual(state['read_sizes'],[7,1,7,1])
        self.assertTrue(proof['existing_workspace_leaf_verified_and_reused'])
        self.assertEqual(chunk.summary(reader)['workspace_allocations'],1)

    def test_same_name_workspace_leaf_without_exact_original_code_is_refused(self):
        _,state,pin,base,_=fixture()
        class ChunkLeaf(original.AuditEvidenceReader):
            def _read(self,name,parse=False):raise AssertionError('UNDECLARED_LEAF')
        class Existing(base,ChunkLeaf):pass
        with self.assertRaisesRegex(ValueError,'EXACT_EXISTING_WORKSPACE_LEAF'):
            candidate.reader_type(Existing,{pin['path']:pin},exact,pressure,original,chunk,RAW)

    def test_real_metadata_weighted_rates_preserved_without_native_policy_change(self):
        _,state,pin,base,_=fixture()
        class Metadata(base):
            def __init__(self,*args,**kwargs):
                super().__init__(*args,**kwargs);self.pacer=pressure.prior.WeightedPacer()
        Reader,proof=candidate.reader_type(Metadata,{pin['path']:pin},exact,pressure,original,chunk,RAW,
            pacer_policy='metadata_weighted')
        reader=Reader('.',lambda:None);clock=Clock()
        reader.pacer.clock=clock.now;reader.pacer.last=clock.now();reader.pacer.sleeper=clock.sleep
        reader.pacer.select('fixture.exe');self.assertEqual(reader.pacer.rate,2621440)
        reader.pacer.select(pin['path']);self.assertEqual(reader.pacer.rate,4194304)
        reader.pin(pin['path']);reader.finish();self.assertEqual(reader.bytes_read,14)
        self.assertEqual(state['read_sizes'],[7,1,7,1])
        self.assertTrue(proof['original_metadata_two_point_five_four_MiB_rates_retained'])
        self.assertTrue(proof['metadata_rate_membership_only_code_inverse'])
        self.assertFalse(proof['original_Native_pacer_or_policy_modified'])
        native=exact.pacer_type(pressure.OwnedPacer)(clock=clock.now,sleeper=clock.sleep)
        native.rate=4194304;native.request_bytes(1)
        with self.assertRaisesRegex(ValueError,'ORIGINAL_ONE_TWO_MIB'):native.reserve(lambda:None)

    def test_metadata_policy_cannot_silently_replace_owned_or_unknown_rates(self):
        _,state,pin,base,_=fixture()
        Reader,_=candidate.reader_type(base,{pin['path']:pin},exact,pressure,original,chunk,RAW,
            pacer_policy='metadata_weighted')
        with self.assertRaisesRegex(ValueError,'FRESH_ORIGINAL_OWNED'):Reader('.',lambda:None)
        with self.assertRaisesRegex(ValueError,'CLOSED_ORIGINAL_PACER_POLICY'):
            candidate.reader_type(base,{pin['path']:pin},exact,pressure,original,chunk,RAW,pacer_policy='arbitrary')
