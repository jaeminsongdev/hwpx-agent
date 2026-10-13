"""P269 실제 표본 경로의 debounce/admission/원 decision 유지 합성8 계약."""
import unittest
from types import SimpleNamespace
from unittest.mock import patch
import qualify_rejected_parent_connection_r2 as m


def sampler(cpu=20,ram=50,commit=20):
    now=[0.0];sleeps=[];calls=[]
    def sleep(delay):sleeps.append(delay);now[0]+=delay
    def sample():
        calls.append(True)
        return dict(system_cpu_percent=cpu,available_ram_percent=ram,commit_used_percent=commit)
    obj=m.OriginalParentSamples(SimpleNamespace(sample=sample),clock=lambda:now[0],sleep=sleep)
    return obj,now,calls,sleeps


class OriginalSamples(unittest.TestCase):
    def test_original_missing_sample_guard_reproduced_without_IO_or_product(self):
        frame_type=type('Frame',(),dict(boundaries=[],check=lambda self:None,
            read_boundary=lambda self,factory,checkpoint:factory(lambda:None).checkpoint()))
        connection=m.ParentConnection(frame_type(),[],94,m.a.NAME,{'synthetic':'original-sample-contract'})
        def parent(task,path,seconds):m.m.p.c.pins(lambda:None)
        with patch.object(m.m.p,'ORIGINAL_RUN',parent),self.assertRaisesRegex(ValueError,'BACKPRESSURE_NO_ORIGINAL_SAMPLE'):
            connection.run(None,m.m.g.observation.Context())
        self.assertFalse(connection.capture.rejected)
    def test_admission_uses_real_supplied_method_twice_not_manufactured_CPU(self):
        obj,now,calls,sleeps=sampler();self.assertEqual(obj.admit(),2)
        self.assertEqual(len(calls),2);self.assertEqual(now[0],1.0)
        self.assertEqual(obj.rows,[dict(system_cpu_percent=20,available_ram_percent=50,commit_used_percent=20)]*2)
        self.assertFalse(obj.summary()['CPU_samples_manufactured']);self.assertIsNone(obj.summary()['Job_CPU_measurement'])
    def test_half_second_debounce_retained(self):
        obj,now,calls,sleeps=sampler();obj.admit();obj.checkpoint();self.assertEqual(len(calls),2)
        now[0]+=.49;obj.checkpoint();self.assertEqual(len(calls),2)
        now[0]+=.02;obj.checkpoint();self.assertEqual(len(calls),3)
    def test_CPU98_four_consecutive_original_decision_not_changed(self):
        obj,now,calls,sleeps=sampler(cpu=98)
        for unused in range(3):now[0]+=.5;obj.observe(True)
        now[0]+=.5
        with self.assertRaisesRegex(ValueError,'^STOP_SUSTAINED_SYSTEM_CPU$'):obj.observe(True)
        self.assertEqual(len(calls),4)
    def test_original_RAM_and_commit_stop_not_swallowed(self):
        for ram,commit,code in ((7,20,'STOP_LOW_AVAILABLE_RAM'),(50,95,'STOP_SYSTEM_COMMIT_PRESSURE')):
            obj,now,calls,sleeps=sampler(ram=ram,commit=commit);now[0]=.5
            with self.subTest(code=code),self.assertRaisesRegex(ValueError,'^'+code+'$'):obj.observe(True)
    def test_original_interval_missing_retry_bound_retained(self):
        obj,now,calls,sleeps=sampler();count=[0]
        def missing():count[0]+=1;raise ValueError('CPU_SAMPLE_INTERVAL_MISSING')
        obj.windows.sample=missing;now[0]=.5
        with self.assertRaisesRegex(ValueError,'^CPU_SAMPLE_INTERVAL_MISSING$'):obj.observe(True)
        self.assertEqual(count[0],6);self.assertEqual(sleeps,[.02]*5)
    def test_small_bound_and_original_parent1200_not_extended(self):
        obj,now,calls,sleeps=sampler();now[0]=1201
        with self.assertRaisesRegex(ValueError,'ORIGINAL_PARENT1200'):obj.checkpoint()
        self.assertEqual(calls,[])
        obj,now,calls,sleeps=sampler()
        for unused in range(16):now[0]+=.5;obj.observe(True)
        with self.assertRaisesRegex(ValueError,'SMALL_PARENT_SAMPLE_BOUND16'):obj.observe(True)
        self.assertEqual(len(calls),16)
    def test_invalid_or_saturated_admission_never_replaced_with_zero(self):
        obj,now,calls,sleeps=sampler(cpu=98)
        with self.assertRaisesRegex(ValueError,'ORIGINAL_PARENT_ALREADY_SATURATED'):obj.admit()
        obj,now,calls,sleeps=sampler(cpu=float('nan'));now[0]=.5
        with self.assertRaisesRegex(ValueError,'STOP_RESOURCE_OBSERVATION_INVALID'):obj.observe(True)
        obj,now,calls,sleeps=sampler();now[0]=float('nan')
        with self.assertRaisesRegex(ValueError,'ORIGINAL_PARENT_CLOCK'):obj.checkpoint()


if __name__=='__main__':unittest.main()
