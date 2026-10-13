"""P268 원 guard/실패 재발생/작은 연결 범위의 합성28 계약. 제품 실행 없음."""
import copy
import io
import json
import threading
import unittest
from types import SimpleNamespace
from unittest.mock import patch
import qualify_rejected_parent_connection as m
import test_deferred_parent_failure as old
import test_locked_runtime_inputs as locks


def trace(checkpoint=None):
    checks=[];checkpoint=(lambda:checks.append(True)) if checkpoint is None else checkpoint
    api=locks.FakeNative();api.pacer.checkpoint=checkpoint
    context=m.m.g.observation.Context()
    resources=SimpleNamespace(lock=threading.Lock(),samples=[dict(system_cpu_percent=20)])
    obj=m.TimedInputLocks(locks.l.ROOT,checkpoint,resources,context,api=api)
    return obj,context,checks


class Timing(unittest.TestCase):
    def test_original_check_called_and_rate_unchanged(self):
        obj,context,checks=trace();obj.check();self.assertEqual(checks,[True]);self.assertEqual(obj.timing_checks,1)
        self.assertEqual(obj.api.pacer.rate,20);self.assertEqual(obj.maximum_seconds,600)
    def test_original_CPU_RAM_and_scope_errors_rethrown(self):
        for code in ('STOP_SUSTAINED_SYSTEM_CPU','STOP_LOW_AVAILABLE_RAM','STOP_SYSTEM_COMMIT_PRESSURE','STOP_SQL_IO_SCOPE_TIME'):
            error=ValueError(code)
            def stop():raise error
            obj,context,checks=trace(stop)
            with self.subTest(code=code),self.assertRaises(ValueError) as caught:obj.check()
            self.assertIs(caught.exception,error);self.assertEqual(obj.timing_first_error['original_error_code'],code)
    def test_first_error_phase_and_original600_recorded(self):
        obj,context,checks=trace();context.phase='final_fresh_hash';obj.started-=601
        with self.assertRaisesRegex(ValueError,'P206_LOCK_DEADLINE_EXCEEDED'):obj.check()
        row=obj.timing_first_error;self.assertEqual(row['phase'],'final_fresh_hash')
        self.assertGreaterEqual(row['original_lock_elapsed_seconds'],601);self.assertEqual(row['original_lock_limit_seconds'],600)
    def test_deadline_prevents_native_acquisition(self):
        obj,context,checks=trace();obj.started-=601
        with self.assertRaises(ValueError):obj.acquire({'tools/p09/mock.py':dict(path='tools/p09/mock.py',bytes=1,sha256='a'*64)})
        self.assertEqual(obj.api.counter,0)
    def test_unknown_elapsed_not_zero_and_original_error_retained(self):
        error=ValueError('STOP_LOW_AVAILABLE_RAM')
        def stop():raise error
        obj,context,checks=trace(stop)
        with patch.object(m.time,'monotonic',return_value=float('nan')),self.assertRaises(ValueError) as caught:obj.check()
        self.assertIs(caught.exception,error);self.assertIsNone(obj.timing_first_error['original_lock_elapsed_seconds'])
    def test_no_extra_clock_in_successful_check(self):
        obj,context,checks=trace()
        with patch.object(m,'time',SimpleNamespace(monotonic=lambda:(_ for _ in ()).throw(AssertionError('NO_EXTRA_CLOCK')))):
            obj.check()
        self.assertIsNone(obj.timing_first_error)
    def test_phase_boundary_records_without_sampling(self):
        obj,context,checks=trace();obj.mark('before_acquire');self.assertEqual(len(obj.timing_events),1)
        self.assertEqual(obj.timing_events[0]['phase'],'admission');self.assertEqual(checks,[True])
    def test_unknown_phase_label_denied(self):
        obj,context,checks=trace()
        with self.assertRaises(ValueError):obj.mark('raw-secret-phase')
        self.assertEqual(checks,[])
    def test_phase_event_storage_bounded(self):
        obj,context,checks=trace()
        for unused in range(16):obj.mark('before_acquire')
        with self.assertRaises(ValueError):obj.mark('before_acquire')
        self.assertEqual(len(obj.timing_events),16)
    def test_cleanup_does_not_invoke_stopped_guard(self):
        obj,context,checks=trace();obj.owned=[('one',None,1,False)];obj.opened_handles=1;obj.api.handles[1]={}
        obj.started-=601
        with patch.object(obj,'checkpoint',side_effect=AssertionError('NO_CLEANUP_GUARD')):
            self.assertTrue(obj.close())
        self.assertEqual(obj.timing_checks,0);self.assertEqual(obj.api.handles,{})
    def test_summary_preserves_original_limits_and_false_claims(self):
        obj,context,checks=trace();row=obj.summary()['lock_timing_diagnostic']
        self.assertEqual(row['original_lock_limit_seconds'],600)
        self.assertFalse(row['original_resource_guard_or_deadline_extended']);self.assertFalse(row['extra_CPU_RAM_or_native_query_started'])
    def test_first_failure_not_replaced_by_later_phase(self):
        obj,context,checks=trace();obj.started-=601
        with self.assertRaises(ValueError):obj.check()
        first=copy.deepcopy(obj.timing_first_error);context.phase='cleanup'
        with self.assertRaises(ValueError):obj.check()
        self.assertEqual(obj.timing_first_error,first)


class Connection(unittest.TestCase):
    def fresh(self):
        frame=old.Frame();return frame,m.ParentConnection(frame,[],94,m.a.NAME,old.BINDING)
    def call(self,connection,reason='OWNED_RUNNER_FAILURE'):
        calls=[];empty=io.StringIO()
        def original(task,destination,seconds):
            calls.append((task,seconds));row=m.fake_original_row(task);row['stop_reason']=reason
            json.dump(row,empty,ensure_ascii=False,indent=2);return 2
        with patch.object(m.m.p,'ORIGINAL_RUN',original):
            if reason=='STOP_SUSTAINED_SYSTEM_CPU':code=connection.run(None,m.m.g.observation.Context());self.assertEqual(code,2)
            else:
                with self.assertRaisesRegex(ValueError,'TERMINAL_FAILURE_EXACT_STOP_NOT_PASS'):connection.run(None,m.m.g.observation.Context())
        self.assertEqual(calls,[('p204-r07-case-094-tests',1200)]);self.assertEqual(empty.getvalue(),'')
    def test_exact_original_bridge_call_and_capture_retained(self):
        frame,connection=self.fresh();self.call(connection);self.assertTrue(connection.capture.rejected)
        self.assertFalse(connection.capture.pending);self.assertEqual(connection.capture._rejected['task'],'p204-r07-case-094-tests')
    def test_original_rejection_and_reason_unchanged(self):
        frame,connection=self.fresh();self.call(connection,'STOP_SQL_IO_SCOPE_TIME')
        self.assertEqual(connection.capture._rejected['stop_reason'],'STOP_SQL_IO_SCOPE_TIME')
    def test_valid_CPU_original_pending_not_generic_diagnostic(self):
        frame,connection=self.fresh();row=old.document();row.update(task='p204-r07-case-094-tests',selected_test_names=[m.a.NAME],test_arguments=m.m.p.v.arguments(m.a.NAME))
        def original(task,destination,seconds):json.dump(row,io.StringIO(),ensure_ascii=False,indent=2);return 2
        with patch.object(m.m.p,'ORIGINAL_RUN',original):self.assertEqual(connection.run(None,m.m.g.observation.Context()),2)
        self.assertTrue(connection.capture.pending);self.assertFalse(connection.capture.rejected)
    def test_PASS_original_writer_still_guards_frame(self):
        frame,connection=self.fresh();empty=io.StringIO();row={'state':'PASS_SCOPED_NOT_GATE','value':'원 PASS'}
        def bridge(*args):m.m.p.RAW_DUMP(row,empty,ensure_ascii=False,indent=2);return 0
        with patch.object(m.m.p,'run_parent',bridge):self.assertEqual(connection.run(None,m.m.g.observation.Context()),0)
        self.assertEqual(old.m.original.packed.unpack(json.loads(empty.getvalue()),lambda:None),row)
        self.assertGreater(frame.check_calls,0);self.assertFalse(connection.capture.rejected)
    def test_no_second_parent_call_after_rejection(self):
        frame,connection=self.fresh();self.call(connection)
        with patch.object(m.m.p,'run_parent',side_effect=AssertionError('NO_RETRY')),self.assertRaises(ValueError):connection.run(None,None)
    def test_invalid_regular_selection_denied(self):
        for index,name in ((True,m.a.NAME),(0,m.a.NAME),(250,m.a.NAME),(94,'../name')):
            with self.assertRaises(ValueError):m.ParentConnection(old.Frame(),[],index,name,old.BINDING)
    def test_foreign_parent_row_not_retained(self):
        frame,connection=self.fresh()
        def original(task,destination,seconds):json.dump(m.fake_original_row('foreign'),io.StringIO(),ensure_ascii=False,indent=2)
        with patch.object(m.m.p,'ORIGINAL_RUN',original),self.assertRaises(ValueError):connection.run(None,m.m.g.observation.Context())
        self.assertFalse(connection.capture.rejected)
    def test_diagnostic_requires_original_rejected_row(self):
        frame,connection=self.fresh();frame.close();owner,out=old.terminal()
        with self.assertRaises(ValueError):connection.write_rejected(io.StringIO(),owner,out)
    def test_no_diagnostic_before_owner_done(self):
        frame,connection=self.fresh();self.call(connection);frame.close();owner,out=old.terminal();owner.done.clear()
        with self.assertRaises(ValueError):connection.write_rejected(io.StringIO(),owner,out)
    def test_no_diagnostic_before_frame_release(self):
        frame,connection=self.fresh();self.call(connection);owner,out=old.terminal()
        with self.assertRaises(ValueError):connection.write_rejected(io.StringIO(),owner,out)
    def test_unknown_original_Job_cleanup_preserved_as_None(self):
        frame,connection=self.fresh();self.call(connection);frame.close();owner,out=old.terminal();stream=io.StringIO()
        connection.write_rejected(stream,owner,out);saved=json.loads(stream.getvalue())
        self.assertIsNone(saved['original_parent_document']['job_final']);self.assertIsNone(saved['original_parent_document']['cleanup_confirmed'])
        self.assertFalse(saved['runtime_accepted']);self.assertTrue(saved['diagnostic_only'])
    def test_parent_RAW_DUMP_patch_restored_after_error(self):
        frame,connection=self.fresh();original=m.m.p.RAW_DUMP;self.call(connection)
        self.assertIs(m.m.p.RAW_DUMP,original)


def probe():
    required={n:dict(path=n,bytes=1,sha256='a'*64) for n in ('tools/p09/a.py','tools/p09/tests/b.py','tools/p09/c.py')}
    timing=dict(first_original_error=None,original_lock_limit_seconds=600,original_guard_checks=10,
        explicit_phase_events=[dict(label=n,original_lock_elapsed_seconds=i) for i,n in enumerate(m.LABELS)],
        extra_CPU_RAM_or_native_query_started=False,original_resource_guard_or_deadline_extended=False,
        cleanup_callback_wrapped=False,CPU_or_PC_freeze_improvement_established=False)
    h=dict(input_lock_handles_opened=7,input_lock_handles_closed=7,input_lock_handles_remaining=0,
        active_reader_bindings=0,active_byte_streams=0,handle_close_failed_attempts=0,input_lock_cleanup_confirmed=True,
        maximum_lock_seconds=600,byte_stream_identity_checks=6,handle_metadata_checks=20,
        native_open_pacing=dict(maximum_opens_per_second=20,open_reservations=13),lock_timing_diagnostic=timing,
        borrowed_byte_streams=dict(duplicate_handles_opened=6,duplicate_handles_closed=6,shared_offset_resets=6,
            duplicate_handles_remaining=0,duplicate_close_failed_attempts=0,byte_stream_pathname_reopens=0))
    snapshot=dict(frame_state='CLOSED',registered_live_frame=False,input_count=3,input_bytes=3,
        held_identity_after_owned_cleanup=None,original_owned_cleanup_confirmed_before_release=False,handles=h,
        actual_byte_boundaries=[dict(role=role,actual_byte_pins=list(required.values()),reader_diagnostics=dict(
            read_passes=3,bytes_read=3,read_rates_by_kind=dict(binary=1048576,other=2097152),
            original_owned_read_operations_preserved=True)) for role in ('before','after')])
    return snapshot,required,timing


class SmallProbeScope(unittest.TestCase):
    def test_small_scope_only_not_runtime_commit(self):
        args=probe();m.validate_probe(*args);self.assertIsNone(args[0]['held_identity_after_owned_cleanup'])
    def test_partial_boundary_not_accepted(self):
        args=probe();args[0]['actual_byte_boundaries'].pop()
        with self.assertRaises(ValueError):m.validate_probe(*args)
    def test_native_guard_and_scope_not_relaxed(self):
        for key,value in (('maximum_lock_seconds',1200),('input_lock_handles_remaining',None),('handle_metadata_checks',0)):
            args=probe();args[0]['handles'][key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):m.validate_probe(*args)
    def test_product_commit_or_missing_timing_not_promoted(self):
        args=probe();args[0]['original_owned_cleanup_confirmed_before_release']=True
        with self.assertRaises(ValueError):m.validate_probe(*args)
        args=probe();args[2]['explicit_phase_events'][0]['original_lock_elapsed_seconds']=None
        with self.assertRaises(ValueError):m.validate_probe(*args)


if __name__=='__main__':unittest.main()
