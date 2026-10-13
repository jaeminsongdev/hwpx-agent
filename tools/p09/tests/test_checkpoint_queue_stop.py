"""P257: 실제 실패 fixture20 + fake표본 조기source checkpoint12. PC stress 없음."""
import copy
import threading
import unittest
from types import SimpleNamespace
import review_checkpoint_queue_stop as p
FIXTURES=None


class StopReviewTests(unittest.TestCase):
    def setUp(self):
        if FIXTURES is None:raise RuntimeError('CURRENT_STOP_FIXTURES_REQUIRED')
        self.root,self.body=copy.deepcopy(FIXTURES)
    def reject(self):
        with self.assertRaises((ValueError,KeyError,TypeError)):p.review(self.root,self.body)
    def test_valid_preserves_body_and_blocks_repeat(self):
        d=p.review(self.root,self.body);self.assertFalse(d['runtime_acceptance_changed'])
        self.assertFalse(d['same_product_body_reexecution_allowed']);self.assertTrue(d['independent_full_source_closing_required'])
    def test_root_pass_rejected(self):self.root['state']=p.m.PASS;self.reject()
    def test_root_stop_null_rejected(self):self.root['resource_stop_reason']=None;self.reject()
    def test_wrong_case_rejected(self):self.root['selected_test_index']=91;self.reject()
    def test_wrong_prior_count_rejected(self):self.root['prior_runtime_plan']['runtime_source_qualified_individual_cases']=84;self.reject()
    def test_wrong_body_phase_rejected(self):self.body['operation_phase']='running';self.reject()
    def test_wrong_stop_rejected(self):self.body['stop_reason']='STOP_LOW_AVAILABLE_RAM';self.reject()
    def test_exit_bool_nonzero_rejected(self):
        for v in (False,1):self.body['exit_code']=v;self.reject()
    def test_wrong_pass_name_rejected(self):self.body['passed_test_names']=['other'];self.reject()
    def test_wrong_filtered_count_rejected(self):self.body['terminal_summary']['filtered_out']=247;self.reject()
    def test_overall_pass_not_invented(self):self.body['tests_passed']=1;self.reject()
    def test_incomplete_capture_rejected(self):self.body['capture']['complete_streams']=False;self.reject()
    def test_received_buffer_mismatch_rejected(self):self.body['capture_diagnostics']['received_bytes']['stdout']+=1;self.reject()
    def test_missing_go_rejected(self):self.body['writer_authorized']=False;self.reject()
    def test_job_live_rejected(self):self.body['job_final']['active_processes']=1;self.reject()
    def test_limits_relaxation_rejected(self):self.body['owned_limits_readback']['cpu_hard_cap_machine_percent']=12.5;self.reject()
    def test_source_subset_rejected(self):self.body['source_freeze'].pop();self.reject()
    def test_partial_after_cannot_be_promoted(self):self.body['owned_source_reader_passes'][1]['read_passes']=1545;self.reject()
    def test_source_or_duplicate_residue_rejected(self):
        self.root['terminal_source_frame']['handles']['input_lock_handles_remaining']=1;self.reject()
        self.root['terminal_source_frame']['handles']['input_lock_handles_remaining']=0
        self.root['terminal_source_frame']['handles']['borrowed_byte_streams']['duplicate_handles_remaining']=1;self.reject()
    def test_gate_or_failure_link_mutation_rejected(self):
        self.root['P09_gate']='PASS';self.reject();self.root['P09_gate']='OPEN'
        self.root['terminal_parent_failure_sidecar_pin']['bytes']+=1;self.reject()


class EarlySourceTests(unittest.TestCase):
    def gate(self,values,*,stop=None,cached=False):
        r=SimpleNamespace(lock=threading.Lock(),samples=[],hot=0);calls=[];sleeps=[];seq=iter(values)
        def base():
            calls.append(True)
            if stop:raise ValueError(stop)
            if cached and r.samples:return
            row=dict(system_cpu_percent=next(seq),available_ram_percent=30,commit_used_percent=40)
            r.hot,reason=p.m.p.c.decision(row,r.hot);r.samples.append(row)
            if reason:raise ValueError(reason)
        return p.EarlySourceCheckpoint(base,r,sleep=sleeps.append),calls,sleeps,r
    def test_below90_not_startup_gate(self):
        g,c,s,r=self.gate((35,89.99));g();g();self.assertEqual(len(c),2);self.assertEqual(s,[])
    def test_observed90_to95_range_yields_earlier(self):
        g,c,s,r=self.gate((90.72,89,88));g();self.assertEqual(len(c),3);self.assertEqual(s,[0.5]*2)
    def test_exact90_yields(self):
        g,c,s,r=self.gate((90,89,88));g();self.assertEqual(g.warning_entries,1)
    def test_two_distinct_cool_windows(self):
        g,c,s,r=self.gate((92,88,93,87,86));g();self.assertEqual(s,[0.5]*4)
    def test_original98_four_guard_never_reset(self):
        g,c,s,r=self.gate((98,99,100,100))
        with self.assertRaisesRegex(ValueError,'STOP_SUSTAINED_SYSTEM_CPU'):g()
        self.assertEqual(r.hot,4);self.assertEqual(len(c),4);self.assertEqual(s,[0.5]*3)
    def test_pause_max8(self):
        g,c,s,r=self.gate((92,)*9)
        with self.assertRaisesRegex(ValueError,'STOP_EARLY_SOURCE_NOT_COOLING'):g()
        self.assertEqual(s,[0.5]*8)
    def test_cached_sample_cannot_qualify(self):
        g,c,s,r=self.gate((92,),cached=True)
        with self.assertRaisesRegex(ValueError,'SOURCE_SAMPLE_NOT_ADVANCED'):g()
    def test_original_RAM_commit_and600_failure_propagate(self):
        for code in ('STOP_LOW_AVAILABLE_RAM','STOP_SYSTEM_COMMIT_PRESSURE','STOP_SQL_IO_SCOPE_TIME'):
            g,c,s,r=self.gate((),stop=code)
            with self.assertRaisesRegex(ValueError,code):g()
            self.assertEqual(s,[])
    def test_invalid_CPU_fails_closed(self):
        for v in (True,float('nan'),-1,101,'90'):
            r=SimpleNamespace(lock=threading.Lock(),samples=[dict(system_cpu_percent=v)])
            g=p.EarlySourceCheckpoint(lambda:None,r,sleep=lambda _:None)
            with self.assertRaisesRegex(ValueError,'SOURCE_CPU_INVALID'):g()
    def test_missing_sample_fails_closed(self):
        r=SimpleNamespace(lock=threading.Lock(),samples=[])
        with self.assertRaisesRegex(ValueError,'SOURCE_SAMPLE_MISSING'):p.EarlySourceCheckpoint(lambda:None,r)()
    def test_summary_no_runtime_or_cause_claim(self):
        g,c,s,r=self.gate((91,89,88));g();d=g.summary();self.assertEqual(d['requested_pause_seconds'],1)
        self.assertFalse(d['new_sampler_or_thread_started']);self.assertFalse(d['CPU_or_PC_freeze_improvement_established'])
    def test_cleanup_is_not_callback_wrapped(self):
        g,c,s,r=self.gate((),stop='STOP_SUSTAINED_SYSTEM_CPU');clean=[]
        try:g()
        except ValueError:clean.append(True)
        self.assertEqual(clean,[True]);self.assertEqual(s,[]);self.assertFalse(g.summary()['cleanup_callback_wrapped'])
