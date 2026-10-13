"""P262: 생성 중 표본/실패/중복/STOP 보존; 실제 91 원 실패를 약화하지 않음."""
import copy
from types import SimpleNamespace as Box
import unittest
import review_monotonic_metadata_observation as v
FIXTURES=None


class AttachmentTests(unittest.TestCase):
    def box(self):
        ctx=v.g.observation.Context();first=Box(bytes_read=100,read_passes=2)
        full=Box(bytes_read=500,read_passes=4);counter=v.p.frames.Counters(first,[full]);ctx.reader=counter
        ctx.snapshot();return ctx,counter
    def test_before_assignment_sample_same_aggregate(self):
        ctx,counter=self.box();adapter=v.AggregateContext(ctx,counter)
        self.assertIs(adapter.reader,counter);self.assertEqual(ctx.snapshot()['audited_logical_read_bytes'],600)
    def test_new_reader_registered_before_constructor_sample(self):
        ctx,counter=self.box()
        class Reader:
            def __init__(self,owner,adapter):
                self.reader=Box(bytes_read=0,read_passes=0);adapter.reader=self.reader
                self.reader.bytes_read=20;self.reader.read_passes=1
                self.sample=adapter.snapshot()
        reader=v.construct(Reader,None,ctx,counter)
        self.assertEqual(reader.sample['audited_logical_read_bytes_delta'],20)
        self.assertEqual(ctx.previous,620);self.assertIs(ctx.reader,counter)
    def test_scope_delegated_to_original_context(self):
        ctx,counter=self.box();adapter=v.AggregateContext(ctx,counter)
        with adapter.scope('metadata_hash'):self.assertEqual(ctx.phase,'metadata_hash')
        self.assertEqual(ctx.phase,'admission')
    def test_duplicate_initial_rejected(self):
        ctx,counter=self.box();adapter=v.AggregateContext(ctx,counter)
        with self.assertRaises(ValueError):adapter.reader=counter.initial
        self.assertEqual(counter.metadata,[])
    def test_duplicate_boundary_rejected(self):
        ctx,counter=self.box();adapter=v.AggregateContext(ctx,counter)
        with self.assertRaises(ValueError):adapter.reader=counter.readers[0]
    def test_duplicate_metadata_rejected(self):
        ctx,counter=self.box();reader=Box(bytes_read=10,read_passes=1);counter.metadata.append(reader)
        with self.assertRaises(ValueError):v.AggregateContext(ctx,counter).reader=reader
    def test_second_assignment_rejected_without_removal(self):
        ctx,counter=self.box();adapter=v.AggregateContext(ctx,counter);reader=Box(bytes_read=2,read_passes=1)
        adapter.reader=reader
        with self.assertRaises(ValueError):adapter.reader=Box(bytes_read=0,read_passes=0)
        self.assertEqual(counter.metadata,[reader])
    def test_missing_counter_does_not_become_zero(self):
        ctx,counter=self.box()
        with self.assertRaises(AttributeError):v.AggregateContext(ctx,counter).reader=Box()
        self.assertEqual(ctx.previous,600)
    def test_invalid_counter_rejected(self):
        for number in (None,True,-1,1.5,'1'):
            ctx,counter=self.box()
            with self.assertRaises(ValueError):v.AggregateContext(ctx,counter).reader=Box(bytes_read=number,read_passes=0)
    def test_original_real_counter_reset_still_fails(self):
        ctx,counter=self.box();adapter=v.AggregateContext(ctx,counter);reader=Box(bytes_read=10,read_passes=1)
        adapter.reader=reader;ctx.snapshot();reader.bytes_read=0
        with self.assertRaisesRegex(ValueError,'READ_COUNTER_RESET'):ctx.snapshot()
    def test_changed_context_binding_rejected(self):
        ctx,counter=self.box();adapter=v.AggregateContext(ctx,counter);ctx.reader=Box(bytes_read=0,read_passes=0)
        with self.assertRaises(ValueError):adapter.reader=Box(bytes_read=0,read_passes=0)
    def test_constructor_failure_cleanup_and_actual_bytes_preserved(self):
        ctx,counter=self.box();clean=[]
        class Reader:
            def __init__(self,owner,adapter):
                self.reader=Box(bytes_read=30,read_passes=1);adapter.reader=self.reader
                self.entry_binding=Box(active=True);raise ValueError('STOP_SUSTAINED_SYSTEM_CPU')
            def close_entry(self):self.entry_binding.active=False;clean.append(True)
        with self.assertRaisesRegex(ValueError,'STOP_SUSTAINED_SYSTEM_CPU'):v.construct(Reader,None,ctx,counter)
        self.assertEqual(clean,[True]);self.assertEqual(counter.bytes_read,630)
        self.assertEqual(ctx.snapshot()['audited_logical_read_bytes_delta'],30)
    def test_factory_without_original_attachment_rejected(self):
        ctx,counter=self.box()
        class Reader:
            def __init__(self,owner,adapter):self.reader=Box(bytes_read=0,read_passes=0)
        with self.assertRaises(ValueError):v.construct(Reader,None,ctx,counter)
    def test_policy_no_sampler_skip_or_freeze_claim(self):
        row=v.policy()
        for key in ('new_sampler_thread_started','read_or_identity_checks_skipped',
                'unknown_measurement_substituted_with_zero','CPU_or_PC_freeze_improvement_established'):
            self.assertFalse(row[key])


class ReviewTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(FIXTURES,'real immutable fixtures required; no skip')
        self.root,self.body=copy.deepcopy(FIXTURES)
    def reject(self):
        with self.assertRaises((ValueError,KeyError,TypeError,IndexError)):v.review(self.root,self.body)
    def test_literal_failure_not_runtime_acceptance(self):
        row=v.review(self.root,self.body);self.assertFalse(row['runtime_acceptance_changed'])
        self.assertFalse(row['same_product_body_reexecution_allowed'])
    def test_cpu_stop_is_different_failure(self):self.root['resource_stop_reason']='STOP_SUSTAINED_SYSTEM_CPU';self.reject()
    def test_failed_root_not_pass(self):self.root['state']=v.old.PASS;self.reject()
    def test_no_frame_commit_forgery(self):self.root['terminal_source_frame']['frame_state']='COMMITTED';self.reject()
    def test_body_single_exact_pass(self):self.body['tests_passed']=2;self.reject()
    def test_body_scope_not_reduced(self):self.body['source_freeze'].pop();self.reject()
    def test_no_handle_residue(self):self.root['terminal_source_frame']['handles']['input_lock_handles_remaining']=1;self.reject()
    def test_no_duplicate_residue(self):self.root['terminal_source_frame']['handles']['borrowed_byte_streams']['duplicate_handles_remaining']=1;self.reject()
    def test_incomplete_metadata_not_fresh(self):self.root['terminal_metadata_IO']['finished']=True;self.reject()
    def test_contract_count_exact(self):self.root['runtime_contract_executions']=497;self.reject()
    def test_no_gate_promotion(self):self.body['P09_gate']='PASS';self.reject()
    def test_job_limits_preserved(self):self.body['owned_limits_verified']=False;self.reject()


if __name__=='__main__':unittest.main()
