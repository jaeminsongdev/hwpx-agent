"""P305: 원95 안쪽 guard90의18계약 + 실제 실패102의12거부조건. 부하 생성 없음."""
import copy
import threading
import unittest
from types import SimpleNamespace as NS
import near_saturation_read_backpressure as old
import leading_metadata_checkpoint_pressure as p
STOP=None
def fixture(values=(20,)):
    rows=[dict(system_cpu_percent=values[0])];remaining=list(values[1:]);events=[]
    owner=NS(samples=rows,lock=threading.Lock())
    def hard():events.append('hard')
    def sleep(s):events.append('sleep');rows.append(dict(system_cpu_percent=remaining.pop(0) if remaining else rows[-1]['system_cpu_percent']))
    pressure=old.PressureCheckpoint(hard,owner,sleep=sleep)
    outer=p.m.early_review.EarlySourceCheckpoint(pressure,owner,sleep=sleep)
    pacer=NS(checkpoint=outer,rate=32,opens=0,previous=None)
    q=NS(resources=owner,finished=False,reader=NS(checkpoint=outer,read_passes=0),
        pressure=pressure,early_metadata_binding=NS(early=outer),entry_binding=NS(pacer=pacer),
        leading_entry_binding=NS(active=True,old95=pressure))
    return q,owner,sleep,events
class BindingTests(unittest.TestCase):
    def test_normal_guard_exactly_once(self):
        q,o,s,e=fixture();b=p.Binding(q,o,sleep=s);q.reader.checkpoint();self.assertEqual(e,['hard']);self.assertEqual(b.calls,1)
    def test_inside95_wait_preempted_at90(self):
        q,o,s,e=fixture((96,89,88));b=p.Binding(q,o,sleep=s);q.reader.checkpoint()
        self.assertEqual(b.early.windows,2);self.assertEqual(q.pressure.warning_entries,0);self.assertEqual(q.early_metadata_binding.early.warning_entries,0)
    def test_mid_read_new_warning(self):
        q,o,s,e=fixture((20,89,88));b=p.Binding(q,o,sleep=s);q.reader.checkpoint();o.samples.append(dict(system_cpu_percent=96))
        q.reader.checkpoint();self.assertEqual(b.early.warning_entries,1);self.assertEqual(q.pressure.warning_entries,0)
    def test_cool_requires_consecutive_new_samples(self):
        q,o,s,e=fixture((96,89,94,89,88));b=p.Binding(q,o,sleep=s);q.reader.checkpoint();self.assertEqual(b.early.windows,4)
    def test_original_hard_STOP_first(self):
        q,o,s,e=fixture((100,));q.pressure.base=lambda:(_ for _ in ()).throw(ValueError('STOP_SUSTAINED_SYSTEM_CPU'));b=p.Binding(q,o,sleep=s)
        with self.assertRaisesRegex(ValueError,'STOP_SUSTAINED_SYSTEM_CPU'):q.reader.checkpoint()
        self.assertEqual(e,[]);self.assertEqual(q.pressure.warning_entries,0)
    def test_original_RAM_guard(self):
        q,o,s,e=fixture();q.pressure.base=lambda:(_ for _ in ()).throw(ValueError('STOP_LOW_AVAILABLE_RAM'));b=p.Binding(q,o,sleep=s)
        with self.assertRaisesRegex(ValueError,'STOP_LOW_AVAILABLE_RAM'):q.reader.checkpoint()
    def test_original_IO600_guard(self):
        q,o,s,e=fixture();q.pressure.base=lambda:(_ for _ in ()).throw(ValueError('STOP_SQL_IO_SCOPE_TIME'));b=p.Binding(q,o,sleep=s)
        with self.assertRaisesRegex(ValueError,'STOP_SQL_IO_SCOPE_TIME'):q.reader.checkpoint()
    def test_hard_guard_after_every_sleep(self):
        q,o,s,e=fixture((96,100))
        def hard():
            e.append('hard')
            if e.count('hard')==2:raise ValueError('STOP_SUSTAINED_SYSTEM_CPU')
        q.pressure.base=hard;b=p.Binding(q,o,sleep=s)
        with self.assertRaisesRegex(ValueError,'STOP_SUSTAINED_SYSTEM_CPU'):q.reader.checkpoint()
        self.assertEqual(e,['hard','sleep','hard'])
    def test_bounded_not_cooling(self):
        q,o,s,e=fixture((96,));b=p.Binding(q,o,sleep=s)
        with self.assertRaises(ValueError):q.reader.checkpoint()
        self.assertEqual(b.early.windows,8)
    def test_stale_sample_rejected(self):
        q,o,s,e=fixture((96,));b=p.Binding(q,o,sleep=lambda s:None)
        with self.assertRaises(ValueError):q.reader.checkpoint()
    def test_unknown_CPU_not_zeroed(self):
        q,o,s,e=fixture((None,));b=p.Binding(q,o,sleep=s)
        with self.assertRaises(ValueError):q.reader.checkpoint()
    def test_callbacks_and_pacer_unchanged(self):
        q,o,s,e=fixture();outer=q.reader.checkpoint;pac=q.entry_binding.pacer;pressure=q.pressure;b=p.Binding(q,o,sleep=s)
        q.reader.checkpoint();self.assertIs(q.reader.checkpoint,outer);self.assertIs(pac.checkpoint,outer);self.assertIs(q.pressure,pressure);self.assertIs(pac,q.entry_binding.pacer)
    def test_close_no_guard(self):
        q,o,s,e=fixture((100,));cb=q.pressure.base;b=p.Binding(q,o,sleep=s);b.close()
        self.assertIs(q.pressure.base,cb);self.assertEqual(e,[])
    def test_double_close(self):
        q,o,s,e=fixture();b=p.Binding(q,o,sleep=s);b.close();b.close();self.assertTrue(b.summary()['hard_callback_restored_after_close'])
    def test_duplicate_binding(self):
        q,o,s,e=fixture();p.Binding(q,o,sleep=s)
        with self.assertRaises(ValueError):p.Binding(q,o,sleep=s)
    def test_wrong_owner(self):
        q,o,s,e=fixture()
        with self.assertRaises(ValueError):p.Binding(q,NS(),sleep=s)
    def test_started_reader(self):
        q,o,s,e=fixture();q.reader.read_passes=1
        with self.assertRaises(ValueError):p.Binding(q,o,sleep=s)
    def test_original_rate_not_relaxed(self):
        q,o,s,e=fixture();q.entry_binding.pacer.rate=33
        with self.assertRaises(ValueError):p.Binding(q,o,sleep=s)
class StopTests(unittest.TestCase):
    def setUp(self):
        if STOP is None:raise RuntimeError('EXACT_FAILED102_REQUIRED')
        self.d=copy.deepcopy(STOP)
    def reject(self):
        with self.assertRaises((ValueError,KeyError,TypeError,IndexError)):p.review_stop(self.d)
    def test_exact_immutable(self):
        before=copy.deepcopy(self.d);r=p.review_stop(self.d);self.assertEqual(self.d,before);self.assertFalse(r['runtime_advance'])
    def test_wrong_stage(self):self.d['failure_diagnostic']['stage']='source_frame_acquire';self.reject()
    def test_wrong_case(self):self.d['selected_test_index']=101;self.reject()
    def test_NO_RuntimePASS(self):self.d['state']='PASS';self.reject()
    def test_native_not_started(self):self.d['terminal_source_frame']={};self.reject()
    def test_body_not_started(self):self.d['actual_product_child_executed']=True;self.reject()
    def test_unconfirmed_cleanup(self):self.d['resource_watcher_cleanup_confirmed']=False;self.reject()
    def test_partial_fresh_not_pass(self):self.d['preparation_IO']['finished']=True;self.reject()
    def test_original_snapshot_not_zeroed(self):self.d['preparation_IO']['final_fresh_hashes']=0;self.reject()
    def test_prior_not_advanced(self):self.d['prior_runtime_plan']['runtime_source_qualified_individual_cases']=96;self.reject()
    def test_own_CPU_not_zeroed(self):self.d['metadata_observation']['samples'][-1]['parent_cpu_machine_percent']=1;self.reject()
    def test_gate_not_promoted(self):self.d['P09_gate']='PASS';self.reject()
if __name__=='__main__':unittest.main()
