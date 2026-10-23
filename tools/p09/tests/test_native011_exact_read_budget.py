"""Candidate rate/EOF/freshness/AST contracts. No Native/product acceptance."""
import hashlib
import io
from pathlib import Path
import unittest
from types import FunctionType,SimpleNamespace as NS
import audit_evidence_io as original
import reusable_audit_chunk_v1 as chunk
import owned_source_read_pressure as pressure
import native011_exact_read_budget as candidate

RAW=(Path(__file__).resolve().parents[3]/candidate.ORIGINAL['path']).read_bytes()


class Clock:
    def __init__(self):self.value=1.;self.sleeps=[]
    def now(self):return self.value
    def sleep(self,delay):self.sleeps.append(delay);self.value+=delay


def fixture(data=b'abc',declared=None,*,workspace=False):
    events=[];state=dict(data=data,reads=0,opens=0,error=False)
    class Stream(io.BytesIO):
        def readinto(self,buffer):
            events.append(('read',len(buffer)));state['reads']+=1
            if state['error']:raise OSError('MODEL_READ_FAILED')
            return super().readinto(buffer[:state.get('fragment',len(buffer))])
    class Source:
        def open(self,mode):
            state['opens']+=1;return Stream(state['data'])
    class Reader(pressure.WeightedReader):
        def _source(self,name):return Source()
    Base=chunk.reader_type(Reader,RAW)[0] if workspace else Reader
    reader=Base('.',lambda:events.append(('check',None)))
    pin=dict(path='model.json',bytes=len(data) if declared is None else declared,sha256=hashlib.sha256(data).hexdigest())
    proof=candidate.attach(reader,{pin['path']:pin},pressure,original,chunk,RAW)
    clock=Clock();reader.pacer.clock=clock.now;reader.pacer.last=clock.now();reader.pacer.sleeper=clock.sleep
    return reader,state,events,pin,proof,clock


class ExactReadContracts(unittest.TestCase):
    def test_original_leaf_inverse_and_all_check_statements_retained(self):
        _,proof=candidate.project(RAW,original,chunk)
        self.assertTrue(proof['entire_original_leaf_AST_inverse'])
        self.assertTrue(proof['all_original_hash_parse_accounting_checkpoint_and_closing_statements_retained'])
        self.assertTrue(proof['actual_EOF_read_retained'])
        with self.assertRaises(ValueError):candidate.project(RAW+b'\n',original,chunk)

    def test_actual_tail_and_real_eof_are_both_reserved_before_fresh_reads(self):
        reader,state,events,pin,_,_=fixture()
        self.assertEqual(reader.fresh_pin(pin['path']),pin)
        self.assertEqual([size for kind,size in events if kind=='read'],[3,1])
        self.assertEqual(reader.pacer.reservations,2);self.assertEqual(reader.pacer.reserved_bytes,4)
        self.assertEqual(reader.pacer.refunded_bytes,1);self.assertEqual(reader.bytes_read,3)
        self.assertEqual(reader.pacer.bytes_paced,3);self.assertIsNone(reader.pacer.pending)

    def test_large_input_limits_every_os_read_and_keeps_same_full_hash(self):
        data=b'a'*(65536*2+17);reader,state,events,pin,_,_=fixture(data)
        self.assertEqual(reader.fresh_pin(pin['path']),pin)
        self.assertEqual([size for kind,size in events if kind=='read'],[65536,65536,17,1])
        self.assertEqual(reader.pacer.bytes_paced,len(data));self.assertEqual(reader.bytes_read,len(data))

    def test_both_boundaries_read_new_bytes_and_do_not_reuse_first_hash(self):
        reader,state,_,pin,_,_=fixture();reader.pin(pin['path']);reader.finish()
        self.assertEqual(reader.read_passes,2);self.assertEqual(reader.final_fresh_hashes,1)
        self.assertEqual(reader.bytes_read,6);self.assertEqual(state['opens'],2)
        reader,state,_,pin,_,_=fixture();reader.pin(pin['path']);state['data']=b'abd'
        with self.assertRaisesRegex(ValueError,'input_changed_during_audit'):reader.finish()

    def test_extra_byte_probe_detects_growth_instead_of_trusting_declared_eof(self):
        reader,state,events,pin,_,_=fixture(b'abcd',declared=3)
        with self.assertRaisesRegex(ValueError,'FRESH_EXTRA_BYTE'):reader.fresh_pin(pin['path'])
        self.assertEqual([n for kind,n in events if kind=='read'],[3,1])
        self.assertEqual(reader.bytes_read,4);self.assertEqual(reader.pacer.bytes_paced,4)
        self.assertTrue(reader.pacer.failed);self.assertEqual(reader.snapshots,{})

    def test_truncation_yields_short_actual_pin_not_synthetic_expected_pin(self):
        reader,state,_,pin,_,_=fixture(b'ab',declared=3)
        actual=reader.fresh_pin(pin['path']);self.assertEqual(actual['bytes'],2)
        self.assertNotEqual(actual,pin);self.assertEqual(reader.bytes_read,2)

    def test_existing_workspace_leaf_is_exact_and_not_duplicated(self):
        reader,state,_,pin,_,_=fixture(workspace=True)
        self.assertEqual(reader.fresh_pin(pin['path']),pin)
        stats=chunk.summary(reader)
        self.assertEqual(stats['workspace_allocations'],1);self.assertEqual(stats['readinto_completed'],2)
        self.assertEqual(stats['returned_bytes'],3);self.assertFalse(stats['active_lease'])

    def test_parse_budget_and_invalid_json_still_fail(self):
        reader,state,_,pin,_,_=fixture(b'not-json')
        with self.assertRaisesRegex(ValueError,'audit_json_invalid'):reader.json(pin['path'])
        reader,state,_,pin,_,_=fixture(b'"long value"');reader.maximum_parse_bytes=2
        with self.assertRaisesRegex(ValueError,'audit_parse_budget_exceeded'):reader.json(pin['path'])
        self.assertTrue(reader.pacer.failed)

    def test_io_failure_is_sticky_and_does_not_open_again(self):
        reader,state,_,pin,_,_=fixture();state['error']=True
        with self.assertRaisesRegex(OSError,'MODEL_READ_FAILED'):reader.fresh_pin(pin['path'])
        before=state['opens'];state['error']=False
        with self.assertRaisesRegex(ValueError,'SAME_UNFAILED'):reader.fresh_pin(pin['path'])
        self.assertEqual(state['opens'],before)

    def test_selected_rates_and_capacity_bound_each_actual_transfer(self):
        clock=Clock();Pacer=candidate.pacer_type(pressure.OwnedPacer)
        p=Pacer(clock=clock.now,sleeper=clock.sleep);total=0;start=clock.now()
        for size in [65536,1,4096,32768,65536,65536,8192]:
            p.select('model.json');p.request_bytes(size);p.reserve(lambda:None);p.refund(size);total+=size
            self.assertLessEqual(total,65536+2097152*(clock.now()-start)+1e-6)
            self.assertTrue(0<=p.tokens<=65536)
        self.assertEqual(p.bytes_by_kind,dict(binary=0,other=total))
        self.assertTrue(all(0<delay<=.05 for delay in clock.sleeps))

    def test_binary_rate_short_refund_and_idle_credit_remain_bounded(self):
        clock=Clock();p=candidate.pacer_type(pressure.OwnedPacer)(clock=clock.now,sleeper=clock.sleep)
        p.select('model.exe');self.assertEqual(p.rate,1048576)
        p.request_bytes(65536);p.reserve(lambda:None);p.refund(1)
        self.assertEqual(p.tokens,65535);clock.value+=100
        p.request_bytes(65536);p.reserve(lambda:None);p.refund(65536)
        self.assertEqual(p.tokens,0);p.request_bytes(65536);p.reserve(lambda:None);p.refund(65536)
        self.assertGreaterEqual(sum(clock.sleeps),.0625-1e-9)

    def test_invalid_or_unreserved_read_accounting_is_rejected(self):
        for bad in (0,65537,True,-1):
            clock=Clock();p=candidate.pacer_type(pressure.OwnedPacer)(clock=clock.now,sleeper=clock.sleep)
            with self.assertRaises(ValueError):p.request_bytes(bad)
        clock=Clock();p=candidate.pacer_type(pressure.OwnedPacer)(clock=clock.now,sleeper=clock.sleep)
        with self.assertRaises(ValueError):p.refund(0)
        self.assertTrue(p.failed)

    def test_original_classes_methods_and_existing_used_reader_untouched(self):
        methods=(pressure.WeightedReader._read,pressure.OwnedPacer.reserve,original.AuditEvidenceReader._read)
        reader,state,_,pin,proof,_=fixture();reader.fresh_pin(pin['path'])
        with self.assertRaises(ValueError):candidate.attach(reader,{pin['path']:pin},pressure,original,chunk,RAW)
        self.assertEqual(methods,(pressure.WeightedReader._read,pressure.OwnedPacer.reserve,original.AuditEvidenceReader._read))
        self.assertFalse(proof['installed_in_product'])

    def test_prepared_helper_retains_no_input_bytes_or_freshness_credit(self):
        bind=candidate.prepare(RAW,pressure,original,chunk)
        class Reader(pressure.WeightedReader):pass
        pin=dict(path='model',bytes=3,sha256=hashlib.sha256(b'abc').hexdigest())
        first=Reader('.',lambda:None);second=Reader('.',lambda:None)
        bind(first,{'model':pin});bind(second,{'model':pin})
        self.assertIsNot(first.pacer,second.pacer);self.assertIsNot(first._exact_input_sizes,second._exact_input_sizes)
        self.assertEqual(first.snapshots,{});self.assertEqual(second.snapshots,{})
        self.assertEqual(first.read_passes+second.read_passes+first.bytes_read+second.bytes_read,0)

    def test_short_reads_continue_until_real_eof_and_hash_all_returned_bytes(self):
        reader,state,_,pin,_,_=fixture(b'abcdefghi');state['fragment']=2
        self.assertEqual(reader.fresh_pin(pin['path']),pin)
        self.assertEqual(state['reads'],6);self.assertEqual(reader.bytes_read,9)
        self.assertEqual(reader.pacer.bytes_paced,9);self.assertEqual(reader.pacer.reservations,6)
    def test_one_read_adapter_reused_without_retaining_stream_or_source_bytes(self):
        reader,state,_,pin,_,_=fixture(b'x'*(65536*2+17));adapter=reader._exact_read_proxy
        reader.pin(pin['path']);reader.finish()
        self.assertIs(reader._exact_read_proxy,adapter)
        self.assertEqual(adapter.calls,8);self.assertEqual(adapter.calls,reader.pacer.reservations)
        self.assertIsNone(adapter.stream);self.assertIsNone(adapter.request)

    def test_original_resource_exception_stops_before_any_stream_open(self):
        reader,state,_,pin,_,_=fixture();error=ValueError('MODEL_ORIGINAL_CPU_STOP')
        def stop():raise error
        reader.checkpoint=stop
        with self.assertRaises(ValueError) as caught:reader.fresh_pin(pin['path'])
        self.assertIs(caught.exception,error);self.assertEqual(state['opens'],0)

    def test_undeclared_input_or_additional_read_wrapper_is_not_bypassed(self):
        reader,state,_,pin,_,_=fixture()
        with self.assertRaisesRegex(ValueError,'DECLARED_INPUT_ONLY'):reader.fresh_pin('not-declared')
        self.assertEqual(state['opens'],0)
        class Wrapper(pressure.WeightedReader):
            def _read(self,*args,**kwargs):return super()._read(*args,**kwargs)
        wrapped=Wrapper('.',lambda:None)
        with self.assertRaisesRegex(ValueError,'NO_UNDECLARED_READ_WRAPPERS'):
            candidate.attach(wrapped,{pin['path']:pin},pressure,original,chunk,RAW)

    def test_original_semantic_envelope_and_decoder_guard_wrap_both_new_readers(self):
        from test_runtime_envelope_frame_connection_v1 import setup
        frame,held,factory,made,binding,semantic=setup()
        pins={name:dict(pin) for name,pin in frame.inputs.items()}
        prepared=candidate.prepare(RAW,pressure,original,chunk)
        def adapted(check):
            reader=factory(check);prepared(reader,pins);return reader
        frame.acquire()
        try:
            first=frame.read_boundary(adapted,lambda:None)
            second=frame.read_boundary(adapted,lambda:None)
            self.assertEqual(first,second);self.assertEqual(frame.decoder_budget.completed,2)
            self.assertEqual(frame.original_boundary_factories,2)
            self.assertTrue(all(r.pacer.bytes_paced==r.bytes_read for r in made))
            self.assertTrue(all(r.envelope_original_boundary_guard_calls>0 for r in made))
        finally:frame.close()
        self.assertEqual(frame.state,'CLOSED');self.assertFalse(held.active_readers)

    def connection_fixture(self):
        class Reader(pressure.WeightedReader):pass
        Reader=chunk.reader_type(Reader,RAW)[0]
        calls=[]
        def previous(*args,**kwargs):calls.append(1);return Reader(*args,**kwargs)
        def run():pass
        env=dict(BoundaryReader=previous,byte_policy=pressure)
        linked=NS(engine=NS(run_owned=FunctionType(run.__code__,env)),state=NS(attempts=0,calls=0))
        pins={'model':dict(path='model',bytes=3,sha256=hashlib.sha256(b'abc').hexdigest())}
        return linked,Reader,pins,calls

    def test_private_factory_uses_existing_workspace_identity_without_io_during_construction(self):
        linked,Reader,pins,calls=self.connection_fixture();env=linked.engine.run_owned.__globals__;before=dict(env)
        connection,proof=candidate.connect_private_factory(linked,Reader,pins,RAW)
        self.assertEqual(calls,[]);self.assertEqual(connection.state.attempts,0)
        self.assertTrue(all(env[key] is value for key,value in before.items() if key!='BoundaryReader'))
        first=env['BoundaryReader']('.',lambda:None);second=env['BoundaryReader']('.',lambda:None)
        self.assertEqual(calls,[1,1]);self.assertIsNot(first.pacer,second.pacer)
        self.assertEqual(first.bytes_read+second.bytes_read,0)
        self.assertTrue(proof['original_workspace_class_identity_retained'])
        with self.assertRaisesRegex(ValueError,'TWO_ORIGINAL_BOUNDARIES'):env['BoundaryReader']('.',lambda:None)

    def test_private_factory_failure_cannot_replay_previous_factory(self):
        linked,Reader,pins,calls=self.connection_fixture()
        connection,_=candidate.connect_private_factory(linked,Reader,pins,RAW)
        with self.assertRaises(TypeError):connection.factory()
        self.assertTrue(connection.state.failed)
        with self.assertRaisesRegex(ValueError,'TWO_ORIGINAL_BOUNDARIES'):connection.factory('.',lambda:None)
        self.assertEqual(calls,[1])

    def test_default_engine_module_or_started_worker_rejects_connection(self):
        linked,Reader,pins,_=self.connection_fixture();linked.state.attempts=1
        with self.assertRaisesRegex(ValueError,'BEFORE_ANY_WORKER'):candidate.connect_private_factory(linked,Reader,pins,RAW)
        linked,Reader,pins,_=self.connection_fixture()
        import types,sys
        module=types.ModuleType('p09_exact_budget_model_module');module.__dict__.update(linked.engine.run_owned.__globals__)
        linked.engine.run_owned=FunctionType(linked.engine.run_owned.__code__,module.__dict__)
        sys.modules[module.__name__]=module
        try:
            with self.assertRaisesRegex(ValueError,'NO_DEFAULT_ENGINE'):candidate.connect_private_factory(linked,Reader,pins,RAW)
        finally:sys.modules.pop(module.__name__)
