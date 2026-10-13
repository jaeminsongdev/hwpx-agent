"""P279 cached-entry16/원STOP6. 원P27032는 qualification에서 별도 유지."""
import copy
import unittest
from types import SimpleNamespace
from unittest.mock import patch
import qualify_metadata_entry_early_pressure as m
from test_early_metadata_pressure import gate
from test_native_open_backpressure import Clock
FIXTURES=None


def reader(values=(),**kw):
    q,owner,calls,sleeps=gate(values,**kw);q.reader.read_passes=q.reader.bytes_read=0
    clock=Clock();pacer=m.runtime.early_review.m.entry.locks.OpenPacer(q.reader.checkpoint,rate=32,
        clock=clock.read,sleeper=clock.sleep)
    entry=SimpleNamespace(pacer=pacer,reader=q.reader,active=True)
    q.entry_binding=entry;q.reader._p246_entry_binding=entry
    m.metadata.Binding(q,owner,sleep=sleeps.append)
    return q,owner,calls,sleeps,clock


class CachedEntryTests(unittest.TestCase):
    def test_original_gap_reproduced_without_native_or_stress(self):
        q,owner,calls,sleeps,clock=reader((92,))
        self.assertIs(q.entry_binding.pacer.checkpoint,q.pressure)
        self.assertIsNot(q.entry_binding.pacer.checkpoint,q.reader.checkpoint)
        q.entry_binding.pacer.reserve();self.assertEqual(sleeps,[]);self.assertEqual(q.entry_binding.pacer.opens,1)
    def test_90_to95_entry_waits_same_early_before_reservation(self):
        q,owner,calls,sleeps,clock=reader((92,89,88));m.Binding(q,owner);q.entry_binding.pacer.reserve()
        self.assertEqual(sleeps,[.5,.5]);self.assertEqual(len(calls),3)
        self.assertEqual(q.entry_binding.pacer.opens,1);self.assertEqual(q.pressure.warning_entries,0)
        self.assertEqual(q.early_metadata_binding.early.warning_entries,1)
    def test_entry_byte_share_exact_existing_early_and_original95(self):
        q,owner,calls,sleeps,clock=reader();base=q.pressure;early=q.reader.checkpoint;m.Binding(q,owner)
        self.assertIs(q.entry_binding.pacer.checkpoint,early);self.assertIs(early.base,base)
        self.assertIs(q.pressure,base)
    def test_no_new35_percent_start_gate(self):
        q,owner,calls,sleeps,clock=reader((35,89.99));m.Binding(q,owner)
        q.entry_binding.pacer.checkpoint();q.reader.checkpoint();self.assertEqual(sleeps,[])
    def test_original_clock_rate_credits_and_counters_unchanged(self):
        q,owner,calls,sleeps,clock=reader();pacer=q.entry_binding.pacer
        original=(pacer.clock,pacer.sleeper,pacer.rate,pacer.previous,pacer.opens,q.reader.read_passes,q.reader.bytes_read)
        m.Binding(q,owner)
        self.assertEqual(original,(pacer.clock,pacer.sleeper,pacer.rate,pacer.previous,pacer.opens,q.reader.read_passes,q.reader.bytes_read))
    def test_duplicate_attach_denied(self):
        q,owner,*unused=reader();m.Binding(q,owner)
        with self.assertRaises(ValueError):m.Binding(q,owner)
    def test_foreign_owner_denied(self):
        q,owner,*unused=reader()
        with self.assertRaises(ValueError):m.Binding(q,SimpleNamespace())
    def test_started_reader_or_entry_not_reconfigured(self):
        for what in ('read','entry'):
            q,owner,*unused=reader()
            if what=='read':q.reader.read_passes=1
            else:q.entry_binding.pacer.opens=1
            with self.assertRaises(ValueError):m.Binding(q,owner)
    def test_wrong_entry_rate_or_callback_denied(self):
        for what in ('rate','callback'):
            q,owner,*unused=reader()
            if what=='rate':q.entry_binding.pacer.rate=20
            else:q.entry_binding.pacer.checkpoint=lambda:None
            with self.assertRaises(ValueError):m.Binding(q,owner)
    def test_inactive_or_foreign_entry_denied(self):
        for what in ('active','reader'):
            q,owner,*unused=reader()
            if what=='active':q.entry_binding.active=False
            else:q.entry_binding.reader=object()
            with self.assertRaises(ValueError):m.Binding(q,owner)
    def test_original98_four_stop_before_entry_open(self):
        q,owner,calls,sleeps,clock=reader((98,99,100,100));m.Binding(q,owner)
        with self.assertRaisesRegex(ValueError,'STOP_SUSTAINED_SYSTEM_CPU'):q.entry_binding.pacer.reserve()
        self.assertEqual(owner.hot,4);self.assertEqual(q.entry_binding.pacer.opens,0)
    def test_original_ram_commit600_and720_errors_preserved(self):
        for reason in ('STOP_LOW_AVAILABLE_RAM','STOP_SYSTEM_COMMIT_PRESSURE','STOP_SQL_IO_SCOPE_TIME','METADATA_READ_CALL_BUDGET720'):
            q,owner,calls,sleeps,clock=reader(stop=reason);m.Binding(q,owner)
            with self.assertRaisesRegex(ValueError,reason):q.entry_binding.pacer.reserve()
            self.assertEqual(q.entry_binding.pacer.opens,0);self.assertEqual(sleeps,[])
    def test_cached_cpu_not_cooling_evidence(self):
        q,owner,calls,sleeps,clock=reader((92,),cached=True);m.Binding(q,owner)
        with self.assertRaisesRegex(ValueError,'SOURCE_SAMPLE_NOT_ADVANCED'):q.entry_binding.pacer.reserve()
    def test_entry_wait_bounded_without_busy_loop(self):
        q,owner,calls,sleeps,clock=reader((92,)*9);m.Binding(q,owner)
        with self.assertRaisesRegex(ValueError,'STOP_EARLY_SOURCE_NOT_COOLING'):q.entry_binding.pacer.reserve()
        self.assertEqual(sleeps,[.5]*8);self.assertEqual(len(calls),9);self.assertEqual(q.entry_binding.pacer.opens,0)
    def test_constructor_failed_attachment_closes_original_entry(self):
        q,owner,calls,sleeps,clock=reader();closed=[];q.close_entry=lambda:closed.append(True)
        q.entry_binding.pacer.rate=20
        def initial(obj,resource,context):obj.__dict__.update(vars(q))
        with patch.object(m.runtime.Reader,'__init__',initial),self.assertRaises(ValueError):m.Reader(owner,object())
        self.assertEqual(closed,[True]);self.assertEqual(calls,[])
    def test_summary_and_cleanup_do_not_query_or_claim_freeze_fixed(self):
        q,owner,calls,sleeps,clock=reader();close=q.close_entry;b=m.Binding(q,owner)
        m.connection_contract(b.summary());q.close_entry();self.assertIs(q.close_entry,close)
        self.assertEqual(calls,[]);self.assertEqual(sleeps,[])


class StopReviewTests(unittest.TestCase):
    def setUp(self):self.doc,self.plan=copy.deepcopy(FIXTURES)
    def reject(self):
        with self.assertRaises((ValueError,KeyError,TypeError)):m.review(self.doc,self.plan)
    def test_literal_stop_not_frame_or_product_pass(self):
        row=m.review(self.doc,self.plan);self.assertFalse(row['acquisition_phase14_or_original_parent_or_product_body_invoked'])
        self.assertEqual(row['accepted_runtime_subset'],88)
    def test_partial_final_fresh_not_finished(self):
        self.doc['preparation_IO']['finished']=True;self.reject()
    def test_missing_frame_not_zero_handles(self):
        self.doc['terminal_source_frame']={};self.reject()
    def test_declared_byte90_not_observed_entry90(self):
        self.doc['preparation_IO']['early_metadata_pressure']['original_early_source_algorithm_statistics']['warning_entries']=1;self.reject()
    def test_unknown_own_cpu_not_zero(self):
        self.doc['metadata_observation']['samples'][-1]['parent_cpu_machine_percent']=None;self.reject()
    def test_body_or_new_progress_not_inferred(self):
        self.plan['runtime_source_qualified_individual_cases']=89;self.reject()


if __name__=='__main__':unittest.main()
