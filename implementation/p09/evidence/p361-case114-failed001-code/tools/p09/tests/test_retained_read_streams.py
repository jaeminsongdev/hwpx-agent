"""Guarded synthetic retained-stream contracts. No actual product acceptance."""
import copy
import json
from pathlib import Path
import sys
from types import SimpleNamespace as NS
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import retained_read_streams as r
import accept_case112_current_epoch as a
import test_borrowed_locked_streams as old
import test_locked_runtime_inputs as fake

CHECKPOINT=lambda:None


class RetainedContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        q=a.AcceptanceReader(r.b.locks.ROOT,CHECKPOINT)
        pin,raw=q._read(r.LOCK_PIN['path'],parse=True);q._bind(r.LOCK_PIN['path'],pin)
        a.exact(pin,r.LOCK_PIN,'ORIGINAL_LOCK_PIN')
        cls.raw=bytes(raw);cls.projected,cls.proof=r.reader_sources_projection(cls.raw);q.finish()
        cls.Locks=r.locks_type(r.b.BorrowedInputLocks,cls.projected)
    def setUp(self):
        CHECKPOINT()
        self.pin=dict(path='tools/p09/mock.py',bytes=1,sha256='a'*64)
        self.native=fake.FakeNative();self.native.pacer.rate=20
        self.api=old.API(self.native)
        self.held=self.Locks(r.b.locks.ROOT,CHECKPOINT,api=self.native,borrow_api=self.api)
        self.held.acquire({self.pin['path']:self.pin})
        self.reader=NS(_source=lambda name:r.b.locks.ROOT/name)
    def tearDown(self):
        self.api.fail=None;self.native.close_fail=False;self.held.checkpoint=CHECKPOINT
        if self.held.borrower:self.held.borrower.identity=lambda:self.held.borrower.owner
        self.held.close();CHECKPOINT()
    def read(self):
        with self.held.reader_sources(self.reader):
            with self.reader._source(self.pin['path']).open('rb') as stream:return stream.read()
    def test_complete_two_reads_fresh_identity_seek_and_one_physical_duplicate(self):
        original=set(self.native.handles)
        self.assertEqual(self.read(),b'abc');self.assertEqual(self.read(),b'abc')
        self.assertEqual(len(set(self.native.handles)-original),1)
        self.assertEqual(self.held.stream_identity_checks,2)
        self.held.verify_two_byte_passes({self.pin['path']:self.pin})
        row=self.held.borrower.summary()
        self.assertEqual((row['duplicate_handles_opened'],row['duplicate_handles_closed'],row['duplicate_handles_remaining']),(1,0,1))
        self.assertEqual((row['shared_offset_resets'],row['logical_read_leases'],row['logical_read_lease_returns']),(2,2,2))
        self.assertEqual((row['new_duplicate_open_reservations'],row['reused_stream_pressure_checkpoints']),(1,1))
        self.assertTrue(self.held.close());self.assertEqual(self.native.handles,{})
        self.assertEqual(self.held.borrower.summary()['duplicate_handles_closed'],1)
    def test_only_original_reservation_statement_routed_all_guards_undo_exact(self):
        self.assertTrue(self.proof['original_reader_binding_AST_restored_exactly'])
        self.assertFalse(self.proof['original_path_identity_binding_and_active_stream_guards_replaced'])
        for raw in (self.raw[:-1],self.raw.replace(b'held.check()',b'held.check(1)')):
            with self.subTest(),self.assertRaises(ValueError):r.reader_sources_projection(raw)
    def test_reuse_runs_original_pressure_callback_without_extra_open_credit(self):
        self.read();calls=[];self.native.pacer.checkpoint=lambda:calls.append(True)
        before=(self.native.pacer.opens,self.native.pacer.previous)
        self.read();self.assertTrue(calls)
        self.assertEqual((self.native.pacer.opens,self.native.pacer.previous),before)
    def test_reuse_original_pressure_stop_cannot_seek_or_expose_bytes(self):
        self.read();before=self.held.borrower.resets
        self.native.pacer.checkpoint=lambda:(_ for _ in ()).throw(ValueError('PRESSURE_STOP'))
        with self.assertRaisesRegex(ValueError,'PRESSURE_STOP'):self.read()
        self.assertEqual(self.held.borrower.resets,before)
    def test_no_pathname_reopen_or_byte_cache(self):
        with patch.object(Path,'open',side_effect=AssertionError('NO_PATH_OPEN')):
            self.assertEqual(self.read(),b'abc')
            self.api.streams[0].seek(0);self.api.streams[0].write(b'xyz')
            self.assertEqual(self.read(),b'xyz')
    def test_original_source_and_resource_guard_before_reuse(self):
        self.read();self.reader._source=lambda _:(_ for _ in ()).throw(ValueError('SOURCE_STOP'))
        with self.assertRaisesRegex(ValueError,'SOURCE_STOP'):self.read()
        self.reader._source=lambda name:r.b.locks.ROOT/name
        self.held.checkpoint=lambda:(_ for _ in ()).throw(ValueError('CPU_STOP'))
        with self.assertRaisesRegex(ValueError,'CPU_STOP'):self.read()
        self.assertEqual(sum(n=='duplicate' for n,_ in self.api.calls),1)
    def test_identity_drift_or_inheritable_still_rejected_on_second_pass(self):
        self.read();handle=self.api.streams[0].native_handle
        original=copy.deepcopy(self.native.handles[handle])
        for key,value in (('identity',[9,9]),('inheritable',True)):
            self.native.handles[handle]=dict(original,**{key:value})
            with self.subTest(),self.assertRaisesRegex(ValueError,'BYTE_STREAM_IDENTITY_DRIFT'):self.read()
        self.native.handles[handle]=original
    def test_every_original_failure_stage_retained_and_cleanup_closed(self):
        for stage in ('duplicate','descriptor','stream','seek'):
            self.setUp();self.api.fail=stage
            with self.subTest(),self.assertRaises((OSError,ValueError)):self.read()
            self.api.fail=None;self.assertTrue(self.held.close());self.assertEqual(self.native.handles,{})
    def test_partial_read_exception_is_not_success_and_physical_cache_closed(self):
        original=self.reader._source
        with self.assertRaises(RuntimeError):
            with self.held.reader_sources(self.reader):
                with self.reader._source(self.pin['path']).open('rb') as stream:
                    stream.read(1);raise RuntimeError('READ_FAILED')
        self.assertIs(self.reader._source,original);self.assertFalse(self.held.active_readers)
        self.assertEqual(self.held.borrower.lease_returns,1)
        self.assertTrue(self.held.close());self.assertEqual(self.native.handles,{})
    def test_total_physical_handle_bound_before_new_duplicate(self):
        with patch.object(r.b.locks,'MAX_HANDLES',len(self.held.owned)):
            with self.assertRaisesRegex(ValueError,'TOTAL_PHYSICAL_HANDLE_CEILING'):self.read()
        self.assertEqual(self.api.calls,[])
    def test_close_failure_does_not_skip_other_retained_streams_or_originals(self):
        self.read();borrower=self.held.borrower
        other=self.api.duplicate(self.held.owned[-1][2]);stream=self.api.stream(self.api.descriptor(other))
        borrower.retained['other']=('stream',stream);borrower.opened+=1
        first=self.api.streams[0];close=self.api.close_stream
        self.api.close_stream=lambda s:False if s is first else close(s)
        self.assertFalse(self.held.close());self.assertTrue(stream.closed)
        self.assertEqual(len(borrower.retained),1);self.assertEqual(len(self.native.handles),1)
        self.api.close_stream=close;self.assertTrue(self.held.close())
    def test_physical_close_failure_retained_even_after_eventual_cleanup(self):
        self.read();self.api.fail='close';self.assertFalse(self.held.close())
        self.assertEqual(len(self.held.borrower.retained),1)
        self.assertFalse(self.held.summary()['input_lock_cleanup_confirmed'])
        self.api.fail=None;self.assertTrue(self.held.close())
        self.assertFalse(self.held.summary()['input_lock_cleanup_confirmed'])
        self.assertEqual(self.native.handles,{})
    def test_nested_streams_bindings_stale_source_and_wrong_owner_rejected(self):
        with self.held.reader_sources(self.reader):
            stale=self.reader._source(self.pin['path'])
            with stale.open('rb'):
                with self.assertRaises(ValueError):
                    with self.reader._source(self.pin['path']).open('rb'):pass
            with self.assertRaises(ValueError):
                with self.held.reader_sources(NS(_source=self.reader._source)):pass
        with self.assertRaises(ValueError):
            with stale.open('rb'):pass
        self.held.borrower.identity=lambda:('wrong',0)
        with self.assertRaises(ValueError):self.read()
    def test_closed_raw_stream_is_never_replaced_or_reopened_for_success(self):
        self.read();self.api.streams[0].close()
        with self.assertRaisesRegex(ValueError,'RETAINED_STREAM_LIVE'):self.read()
        self.assertEqual(sum(n=='duplicate' for n,_ in self.api.calls),1)
    def test_cost_removed_real_second_open_only_not_bytes_margin_or_deadline(self):
        import current_stored_runtime_scope as scope
        required={self.pin['path']:self.pin,'bin.exe':dict(path='bin.exe',bytes=1048576,sha256='a'*64)}
        baseline=scope.cost(required,14);model=r.model(required,167)
        self.assertEqual(model['two_actual_byte_pass_native_reservations'],2)
        self.assertEqual(model['two_actual_byte_pass_nominal_seconds'],baseline['two_actual_byte_pass_nominal_seconds'])
        self.assertEqual(model['all_native_byte_open_pacing_seconds'],2/20)
        self.assertEqual(model['unallocated_margin_seconds'],60)
        self.assertEqual(model['unchanged_lock_deadline_seconds'],600)
        self.assertEqual(model['predicted_combined_seconds'],baseline['predicted_combined_seconds']-2/20)
    def test_open_cannot_bypass_the_explicit_original_reservation_adapter(self):
        self.read();borrower=self.held.borrower
        with borrower.sources(self.reader):
            self.reader._p206_input_lock_owner=self.held;self.held.active_readers.add(id(self.reader))
            try:
                with self.assertRaisesRegex(ValueError,'EXACT_RESERVED_HELD_PATH'):
                    with borrower.open(r.b.locks.ROOT/self.pin['path'],'rb'):pass
            finally:del self.reader._p206_input_lock_owner;self.held.active_readers.clear()


if __name__=='__main__':
    guard=a.Guard();result=None
    try:
        guard.acquire();CHECKPOINT=guard.check
        result=unittest.TextTestRunner(verbosity=1).run(unittest.defaultTestLoader.loadTestsFromTestCase(RetainedContracts))
    finally:guard.close()
    print(json.dumps(dict(contract_count=result.testsRun if result else 0,passed=bool(result and result.wasSuccessful()),
        cleanup_confirmed=guard.cleanup,actual_product_or_Native_test=False,synthetic_only=True)))
    raise SystemExit(0 if result and result.wasSuccessful() and guard.cleanup else 2)
