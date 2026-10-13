import unittest
from types import SimpleNamespace
from unittest.mock import patch
import metadata_read_entry_pacing as m
import lower_native_acquisition_pressure as lower
from test_native_open_backpressure import Clock


def fixture():
    clock=Clock();calls=[];guard=[];result=object()
    class Reader:
        def __init__(self):self.read_passes=0;self.checkpoint=lambda:guard.append(True);self.snapshots={}
        def _read(self,name,parse=False):
            calls.append((name,parse));self.read_passes+=1;return result
    reader=Reader();binding=m.Binding(reader,clock=clock.read,sleeper=clock.sleep)
    return reader,binding,clock,calls,guard,result


class MetadataEntryTests(unittest.TestCase):
    def test_exact_original_result_and_parse(self):
        reader,b,_,calls,_,result=fixture()
        with b:self.assertIs(reader._read('small',parse=True),result)
        self.assertEqual(calls,[('small',True)]);self.assertEqual(b.completed,1)
    def test_repeated_fresh_reads_not_substituted(self):
        reader,b,_,calls,_,_=fixture();reader.snapshots['small']={'bytes':1}
        with b:reader._read('small');reader._read('small')
        self.assertEqual(len(calls),2);self.assertEqual(reader.read_passes,2)
    def test_idle_does_not_accumulate_entry_burst(self):
        reader,b,clock,_,_,_=fixture()
        with b:
            reader._read('one');clock.now+=10;reader._read('two');before=clock.now;reader._read('three')
        self.assertAlmostEqual(clock.now-before,1/32)
    def test_CPU_stop_before_original_read(self):
        reader,_,clock,calls,_,_=fixture();reader.checkpoint=lambda:(_ for _ in ()).throw(ValueError('STOP_SUSTAINED_SYSTEM_CPU'))
        b=m.Binding(reader,clock=clock.read,sleeper=clock.sleep)
        with self.assertRaisesRegex(ValueError,'STOP_SUSTAINED_SYSTEM_CPU'):
            with b:reader._read('one')
        self.assertEqual(calls,[]);self.assertEqual(b.pacer.opens,0);self.assertFalse(b.active)
    def test_other_original_stops_not_swallowed(self):
        for reason in ('STOP_LOW_AVAILABLE_RAM','STOP_SYSTEM_COMMIT_PRESSURE','STOP_SQL_IO_SCOPE_TIME'):
            reader,_,clock,calls,_,_=fixture()
            def stop(reason=reason):raise ValueError(reason)
            reader.checkpoint=stop;b=m.Binding(reader,clock=clock.read,sleeper=clock.sleep)
            with self.assertRaisesRegex(ValueError,reason):
                with b:reader._read('one')
            self.assertEqual(calls,[])
    def test_original_read_exception_and_restore(self):
        reader,_,clock,_,_,_=fixture()
        def failed(name,parse=False):raise OSError('synthetic_read_failure')
        reader._read=failed;b=m.Binding(reader,clock=clock.read,sleeper=clock.sleep)
        with self.assertRaises(OSError):
            with b:reader._read('one')
        self.assertIs(reader._read,failed);self.assertEqual(b.failed,1)
    def test_cleanup_no_guard_sleep_or_read(self):
        reader,b,clock,calls,guard,_=fixture()
        with b:pass
        self.assertEqual((clock.sleeps,calls,guard),([],[],[]))
        self.assertNotIn('_read',vars(reader));self.assertFalse(b.active)
    def test_used_reader_not_bound(self):
        reader,_,_,_,_,_=fixture();reader.read_passes=1
        with self.assertRaises(ValueError):m.Binding(reader)
    def test_no_second_active_binding(self):
        reader,b,_,_,_,_=fixture()
        with b:
            with self.assertRaises(ValueError):m.Binding(reader)
    def test_detached_wrapper_cannot_continue(self):
        reader,b,_,_,_,_=fixture()
        with b:leaked=reader._read
        with self.assertRaises(ValueError):leaked('one')
    def test_original_byte_pacer_not_replaced_or_global_changed(self):
        reader,b,_,_,_,_=fixture();reader.pacer=object();byte_pacer=reader.pacer
        with b:reader._read('small')
        self.assertIs(reader.pacer,byte_pacer);self.assertEqual(m.locks.MAX_OPENS_PER_SECOND,32)
    def test_summary_no_CPU_claim_or_skip(self):
        _,b,_,_,_,_=fixture();row=b.summary()
        self.assertFalse(row['original_reads_skipped']);self.assertFalse(row['measured_CPU_or_PC_freeze_improvement_claimed'])
        self.assertTrue(row['cleanup_not_guarded_or_paced'])
    def test_combined_scope_budget_no_deadline_extension(self):
        budget=m.estimate_budget(lower.estimate(1525,14216704,104805351,119.5))
        self.assertLess(budget['predicted_combined_seconds_with_allowances'],600)
        self.assertEqual(budget['unchanged_IO_scope_seconds'],600)
        self.assertTrue(budget['all_bounds_must_be_enforced_when_runtime_connected'])
    def test_bad_original_scope_budget_rejected(self):
        budget=lower.estimate(1525,14216704,104805351,119.5);budget['original_total_bytes']=1
        with self.assertRaises(ValueError):m.estimate_budget(budget)
    def test_excessive_time_budget_rejected_not_guard_relaxed(self):
        budget=lower.estimate(1525,14216704,104805351,119.5);budget['metadata_allowance_seconds']=600
        with self.assertRaises(ValueError):m.estimate_budget(budget)
