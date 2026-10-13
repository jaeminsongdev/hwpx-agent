"""P275 신규26+원lower6. 실제 제품/전체 입력 검증 아님."""
import copy
import math
import threading
import unittest
from types import SimpleNamespace
from unittest.mock import patch
import qualify_acquisition_phase_pressure as m
from test_locked_runtime_inputs import FakeNative

FIXTURES=None


class PacerNative(FakeNative):
    def __init__(self):
        super().__init__();self.rates=[]
        # 가짜 clock도 양의 sleep에서 실제 clock처럼 전진. 부동소수점 ULP 정체를 피한다.
        self.pacer.sleeper=lambda delay:setattr(self,'now',math.nextafter(self.now+delay,math.inf))
    def open(self,path,directory):
        self.pacer.reserve();self.rates.append(self.pacer.rate)
        return super().open(path,directory)


def held(checkpoint=None):
    api=PacerNative();calls=[]
    base=(lambda:calls.append(True)) if checkpoint is None else checkpoint
    api.pacer.checkpoint=base
    owner=SimpleNamespace(lock=threading.Lock(),samples=[dict(system_cpu_percent=20)])
    obj=m.InputLocks(m.p.c.ROOT,base,owner,SimpleNamespace(phase='qualification'),api=api,pressure_sleep=lambda delay:None)
    return obj,api,calls


class PhaseTests(unittest.TestCase):
    def setUp(self):
        self.pin=dict(path='tools/p09/mock.py',bytes=1,sha256='a'*64)
        self.inputs={self.pin['path']:self.pin}
    def test_existing_single_pacer_identity(self):
        obj,api,_=held();self.assertIs(obj.api.pacer,api.pacer);self.assertEqual(api.pacer.rate,20)
        self.assertIs(api.pacer.checkpoint,obj.open_pressure)
    def test_only_acquisition14_success_restores20(self):
        obj,api,_=held();obj.acquire(self.inputs)
        self.assertEqual(api.rates,[14]*4);self.assertEqual(api.pacer.rate,20);self.assertTrue(obj.phase_complete);obj.close()
    def test_phase_counts_original_reservations(self):
        obj,api,_=held();obj.acquire(self.inputs);m.phase_contract(obj.summary()['acquisition_phase_pressure'],4,True)
        self.assertEqual(api.pacer.opens,4);obj.close()
    def test_no_clock_or_counter_reset_at_boundary(self):
        obj,api,_=held();obj.acquire(self.inputs);previous=api.pacer.previous;count=api.pacer.opens
        self.assertEqual(previous,api.now);self.assertEqual(count,4);obj.close()
    def test_byte_reservation_remains20_without_idle_burst(self):
        obj,api,_=held();obj.acquire(self.inputs);before=api.now;api.pacer.reserve()
        self.assertAlmostEqual(api.now-before,1/20);self.assertEqual(api.pacer.opens,5);obj.close()
    def test_acquisition_no_burst_after_idle(self):
        obj,api,_=held()
        def acquisition(unused,rows):
            api.pacer.reserve();api.now+=100;api.pacer.reserve();before=api.now;api.pacer.reserve()
            self.assertAlmostEqual(api.now-before,1/14);return obj
        with patch.object(m.runtime.connection.TimedInputLocks,'acquire',acquisition):obj.acquire(self.inputs)
        self.assertEqual(api.pacer.opens,3);self.assertEqual(api.pacer.rate,20);obj.close()
    def test_second_acquisition_denied_without_rate_mutation(self):
        obj,api,_=held();obj.acquire(self.inputs)
        with self.assertRaises(ValueError):obj.acquire(self.inputs)
        self.assertEqual(api.pacer.rate,20);obj.close()
    def test_used_pacer_denied_before_acquisition(self):
        obj,api,_=held();api.pacer.reserve()
        with self.assertRaises(ValueError):obj.acquire(self.inputs)
        self.assertEqual(api.pacer.rate,20);obj.close()
    def test_original_cpu_stop_same_error_restores20(self):
        error=ValueError(m.STOP)
        def stop():raise error
        obj,api,_=held(stop)
        with self.assertRaises(ValueError) as caught:obj.acquire(self.inputs)
        self.assertIs(caught.exception,error);self.assertEqual(api.pacer.rate,20);self.assertFalse(obj.phase_complete);obj.close()
    def test_original_ram_commit_and_io_stop_retained(self):
        for reason in ('STOP_LOW_AVAILABLE_RAM','STOP_SYSTEM_COMMIT_PRESSURE','STOP_SQL_IO_SCOPE_TIME'):
            error=ValueError(reason)
            def stop():raise error
            obj,api,_=held(stop)
            with self.assertRaises(ValueError) as caught:obj.acquire(self.inputs)
            self.assertIs(caught.exception,error);self.assertEqual(api.pacer.rate,20);obj.close()
    def test_original600_deadline_not_extended(self):
        obj,api,_=held();obj.started-=601
        with self.assertRaisesRegex(ValueError,'DEADLINE_EXCEEDED'):obj.acquire(self.inputs)
        self.assertEqual(api.rates,[]);self.assertEqual(api.pacer.rate,20);obj.close()
    def test_native_open_failure_all_original_cleanup(self):
        obj,api,_=held();api.fail_name='mock.py'
        with self.assertRaisesRegex(ValueError,'MOCK_OPEN_FAILURE'):obj.acquire(self.inputs)
        self.assertEqual(api.handles,{});self.assertTrue(obj.closed);self.assertEqual(api.pacer.rate,20)
    def test_reparse_inheritable_and_size_guards_not_removed(self):
        for kind in ('reparse','inheritable','size'):
            obj,api,_=held();api.bad=kind
            with self.assertRaises(ValueError):obj.acquire(self.inputs)
            self.assertEqual(api.handles,{});self.assertEqual(api.pacer.rate,20)
    def test_final_held_identity_drift_not_removed(self):
        obj,api,_=held();obj.acquire(self.inputs);api.handles[1]['identity']=[2,99]
        with self.assertRaisesRegex(ValueError,'HELD_IDENTITY_DRIFT'):obj.verify_held_identities()
        obj.close()
    def test_original_cleanup_not_guarded_or_paced(self):
        obj,api,calls=held();obj.acquire(self.inputs);before=len(calls);now=api.now
        obj.checkpoint=lambda:(_ for _ in ()).throw(AssertionError('NO_CLEANUP_GUARD'))
        self.assertTrue(obj.close());self.assertEqual(len(calls),before);self.assertEqual(api.now,now)
    def test_cleanup_failure_not_pass(self):
        obj,api,_=held();obj.acquire(self.inputs);api.close_fail=True
        self.assertFalse(obj.close());self.assertFalse(obj.summary()['input_lock_cleanup_confirmed'])
        api.close_fail=False;obj.close()
    def test_clock_callback_or_pacer_replacement_denied(self):
        for name in ('clock','checkpoint','sleeper'):
            obj,api,_=held();setattr(api.pacer,name,lambda *args:None)
            with self.assertRaises(ValueError):obj.acquire(self.inputs)
            self.assertEqual(api.pacer.rate,20);obj.close()
    def test_full_future_budget_retains600_and_all_inputs(self):
        value=m.budget(1583,14216704,119639255-14216704+1048576)
        self.assertLess(value['nominal_seconds'],600);self.assertEqual(value['original_IO_scope_seconds'],600)
        self.assertEqual(value['original_shared_metadata_read_limit'],720);self.assertFalse(value['input_or_byte_checks_removed'])
    def test_unknown_or_larger_future_budget_denied(self):
        for count,binary,other in ((1584,14216704,1000),(1578,14216704,1000),(True,14216704,1000),
            (1583,0,1000),(1583,14216704,False),(1583,14216704,119639255)):
            with self.assertRaises(ValueError):m.budget(count,binary,other)
    def test_no_freeze_or_extra_sampler_claim(self):
        obj,api,_=held();obj.acquire(self.inputs);row=obj.summary()['acquisition_phase_pressure']
        self.assertFalse(row['CPU_or_PC_freeze_improvement_established']);self.assertFalse(row['extra_sampler_or_thread_started'])
        self.assertFalse(row['clock_previous_credit_or_reservation_counter_reset']);obj.close()


class ReviewTests(unittest.TestCase):
    def setUp(self):self.root,self.plan=copy.deepcopy(FIXTURES)
    def reject(self):
        with self.assertRaises((ValueError,KeyError,TypeError)):m.review(self.root,self.plan)
    def test_literal_stop_review_not_acceptance(self):
        value=m.review(self.root,self.plan);self.assertFalse(value['failed95_accepted'])
        self.assertIsNone(value['original_duplicate_measurement']);self.assertEqual(value['runtime_accepted'],88)
    def test_partial737_not_full_or_remaining_handle(self):
        self.root['terminal_source_frame']['handles']['input_lock_handles_remaining']=1;self.reject()
    def test_unknown_duplicates_not_manufactured_zero(self):
        self.root['terminal_source_frame']['handles']['borrowed_byte_streams']={};self.reject()
    def test_product_executed_claim_denied(self):
        self.root['actual_product_child_executed']=True;self.reject()
    def test_last_four_causal_cpu_zero_not_invented(self):
        self.root['metadata_observation']['samples'][-1]['parent_cpu_machine_percent']=None;self.reject()
    def test_cleanup_failure_or_gate_not_promoted(self):
        self.root['resource_watcher_cleanup_confirmed']=False;self.reject()


if __name__=='__main__':unittest.main()
