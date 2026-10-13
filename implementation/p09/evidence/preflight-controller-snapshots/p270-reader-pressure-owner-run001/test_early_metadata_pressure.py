"""P270 attachment14 + 원 경고 receipt 거부4; 원 EarlySource12 별도 유지."""
import copy
import threading
import unittest
from types import SimpleNamespace
from unittest.mock import patch
import qualify_early_metadata_pressure as m
import near_saturation_read_backpressure as pressure
FIXTURES=None


def gate(values,stop=None,cached=False):
    rows=SimpleNamespace(lock=threading.Lock(),samples=[],hot=0);calls=[];sleeps=[];seq=iter(values)
    def base():
        calls.append(True)
        if stop:raise ValueError(stop)
        if cached and rows.samples:return
        row=dict(system_cpu_percent=next(seq),available_ram_percent=40,commit_used_percent=30)
        rows.hot,reason=m.m.p.c.decision(row,rows.hot);rows.samples.append(row)
        if reason:raise ValueError(reason)
    original=pressure.PressureCheckpoint(base,rows,sleep=sleeps.append)
    reader=SimpleNamespace(checkpoint=original,pressure=original,bytes_read=42,read_passes=11)
    close=lambda:None
    q=SimpleNamespace(resources=rows,finished=False,reader=reader,close_entry=close,context=object())
    return q,rows,calls,sleeps


class Attachment(unittest.TestCase):
    def test_original95_retained_by_identity(self):
        q,owner,calls,sleeps=gate((20,));old=q.reader.checkpoint;b=m.Binding(q,owner,sleep=sleeps.append)
        self.assertIs(b.original,old);self.assertIs(b.early.base,old);self.assertIs(q.reader.pressure,old)
    def test_90_to95_window_yields_before_old95(self):
        q,owner,calls,sleeps=gate((91.21,89,88));b=m.Binding(q,owner,sleep=sleeps.append);q.reader.checkpoint()
        self.assertEqual(sleeps,[.5,.5]);self.assertEqual(b.early.warning_entries,1)
        self.assertEqual(q.reader.pressure.warning_entries,0);self.assertEqual(len(calls),3)
    def test_normal_background_load_not_new_startup_gate(self):
        q,owner,calls,sleeps=gate((35,89.99));m.Binding(q,owner,sleep=sleeps.append)
        q.reader.checkpoint();q.reader.checkpoint();self.assertEqual(sleeps,[])
    def test_original_CPU98_four_samples_not_reset_or_suppressed(self):
        q,owner,calls,sleeps=gate((98,99,100,100));m.Binding(q,owner,sleep=sleeps.append)
        with self.assertRaisesRegex(ValueError,'STOP_SUSTAINED_SYSTEM_CPU'):q.reader.checkpoint()
        self.assertEqual(owner.hot,4);self.assertEqual(len(calls),4)
    def test_original_RAM_commit600_and720_errors_preserved(self):
        for code in ('STOP_LOW_AVAILABLE_RAM','STOP_SYSTEM_COMMIT_PRESSURE','STOP_SQL_IO_SCOPE_TIME','METADATA_READ_CALL_BUDGET720'):
            q,owner,calls,sleeps=gate((),stop=code);m.Binding(q,owner,sleep=sleeps.append)
            with self.subTest(code=code),self.assertRaisesRegex(ValueError,code):q.reader.checkpoint()
            self.assertEqual(sleeps,[])
    def test_counter_context_and_original_reader_unchanged(self):
        q,owner,calls,sleeps=gate((20,));r=q.reader;c=q.context;m.Binding(q,owner,sleep=sleeps.append)
        self.assertIs(q.reader,r);self.assertIs(q.context,c);self.assertEqual((r.bytes_read,r.read_passes),(42,11))
    def test_cleanup_not_wrapped_or_guarded(self):
        q,owner,calls,sleeps=gate((),stop='STOP_SUSTAINED_SYSTEM_CPU');close=q.close_entry
        m.Binding(q,owner,sleep=sleeps.append);q.close_entry();self.assertIs(q.close_entry,close);self.assertEqual(calls,[])
    def test_duplicate_attach_denied(self):
        q,owner,calls,sleeps=gate(());m.Binding(q,owner,sleep=sleeps.append)
        with self.assertRaises(ValueError):m.Binding(q,owner,sleep=sleeps.append)
    def test_foreign_owner_denied(self):
        q,owner,calls,sleeps=gate(())
        with self.assertRaises(ValueError):m.Binding(q,SimpleNamespace(),sleep=sleeps.append)
    def test_finished_or_replaced_original95_denied(self):
        q,owner,calls,sleeps=gate(());q.finished=True
        with self.assertRaises(ValueError):m.Binding(q,owner,sleep=sleeps.append)
        q,owner,calls,sleeps=gate(());q.reader.checkpoint=lambda:None
        with self.assertRaises(ValueError):m.Binding(q,owner,sleep=sleeps.append)
    def test_cached_sample_cannot_qualify_cooling(self):
        q,owner,calls,sleeps=gate((92,),cached=True);m.Binding(q,owner,sleep=sleeps.append)
        with self.assertRaisesRegex(ValueError,'SOURCE_SAMPLE_NOT_ADVANCED'):q.reader.checkpoint()
    def test_constructor_original_path_runs_before_attachment(self):
        q,owner,calls,sleeps=gate(());observed=[]
        def init(obj,resource,context):
            observed.append(hasattr(obj,'early_metadata_binding'))
            obj.reader=q.reader;obj.resources=owner;obj.finished=False
        with patch.object(m.m.m.Reader,'__init__',init):result=m.Reader(owner,object())
        self.assertEqual(observed,[False]);self.assertIs(result.reader,q.reader)
        self.assertIs(result.reader.checkpoint,result.early_metadata_binding.early)
    def test_bounded_cooling_not_infinite_busy_loop(self):
        q,owner,calls,sleeps=gate((92,)*9);m.Binding(q,owner,sleep=sleeps.append)
        with self.assertRaisesRegex(ValueError,'STOP_EARLY_SOURCE_NOT_COOLING'):q.reader.checkpoint()
        self.assertEqual(sleeps,[.5]*8);self.assertEqual(len(calls),9)
    def test_summary_has_no_skip_extension_or_improvement_claim(self):
        q,owner,calls,sleeps=gate(());row=m.Binding(q,owner,sleep=sleeps.append).summary()
        for name in ('CPU_RAM600_or720_guard_extended','cleanup_callback_wrapped','new_sampler_or_thread_started',
                'source_byte_or_identity_checks_skipped','CPU_or_PC_freeze_improvement_established','reader_or_aggregate_counter_replaced'):
            self.assertFalse(row[name])


class WarningReceipt(unittest.TestCase):
    def fresh(self):
        self.assertIsNotNone(FIXTURES);return copy.deepcopy(FIXTURES)
    def test_exact_warning_not_cause_or_runtime_PASS(self):
        row=m.review(self.fresh());self.assertFalse(row['runtime_acceptance_changed'])
        self.assertFalse(row['reading_cause_or_external_PID_established'])
    def test_failed_or_STOP_not_closed_warning(self):
        row=self.fresh();row['resource_stop_reason']='STOP_SUSTAINED_SYSTEM_CPU'
        with self.assertRaises(ValueError):m.review(row)
    def test_small_scope_not_full_runtime_or_real94_retry(self):
        row=self.fresh();row['actual_current_case94_reexecuted']=True
        with self.assertRaises(ValueError):m.review(row)
    def test_unknown_or_modified_CPU_not_zeroed(self):
        row=self.fresh();row['metadata_observation']['samples'][0]['system_cpu_percent']=None
        with self.assertRaises((ValueError,KeyError,TypeError)):m.review(row)


if __name__=='__main__':unittest.main()
