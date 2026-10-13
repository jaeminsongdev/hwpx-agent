import threading
import unittest
from types import SimpleNamespace
from unittest.mock import patch
import lower_native_acquisition_pressure as m
from test_native_open_backpressure import Clock


def held():
    clock=Clock();rows=SimpleNamespace(lock=threading.Lock(),samples=[dict(system_cpu_percent=20)])
    calls=[];pacer=m.original.borrowed.locks.OpenPacer(lambda:calls.append(True),clock=clock.read,sleeper=clock.sleep)
    api=SimpleNamespace(pacer=pacer,close=lambda handle:True)
    obj=m.InputLocks(m.original.borrowed.locks.ROOT,pacer.checkpoint,rows,api=api,pressure_sleep=clock.sleep)
    return obj,clock,calls


class LowerNativeTests(unittest.TestCase):
    def test_only_instance_rate_changed_and_identity_checkpoint_kept(self):
        obj,_,_=held();self.assertEqual(obj.api.pacer.rate,20)
        self.assertIs(obj.api.pacer.checkpoint,obj.open_pressure)
        self.assertEqual(m.original.borrowed.locks.MAX_OPENS_PER_SECOND,32)
    def test_no_idle_burst_and_one_reservation_per_50ms(self):
        obj,clock,calls=held();obj.api.pacer.reserve();clock.now+=10;obj.api.pacer.reserve()
        before=clock.now;obj.api.pacer.reserve();self.assertAlmostEqual(clock.now-before,0.05)
        self.assertTrue(calls);self.assertEqual(obj.api.pacer.opens,3)
    def test_CPU_and_other_original_stops_not_swallowed(self):
        for reason in ('STOP_SUSTAINED_SYSTEM_CPU','STOP_LOW_AVAILABLE_RAM','STOP_SYSTEM_COMMIT_PRESSURE','STOP_SQL_IO_SCOPE_TIME'):
            obj,_,_=held()
            with patch.object(obj,'checkpoint',side_effect=ValueError(reason)):
                with self.assertRaisesRegex(ValueError,reason):obj.api.pacer.reserve()
            self.assertEqual(obj.api.pacer.opens,0)
    def test_cleanup_no_new_resource_or_pressure_checkpoint(self):
        obj,clock,calls=held();obj.owned=[('one',None,1,False)];obj.opened_handles=1
        self.assertTrue(obj.close());self.assertEqual(calls,[]);self.assertEqual(clock.sleeps,[])
    def test_repeated_or_used_pacer_not_reconfigured(self):
        obj,clock,_=held();obj.api.pacer.reserve()
        with self.assertRaises(ValueError):m.InputLocks(obj.root,obj.api.pacer.checkpoint,
            SimpleNamespace(lock=threading.Lock(),samples=[dict(system_cpu_percent=20)]),api=obj.api)
    def test_budget_must_fit600_without_extension_or_skip(self):
        result=m.estimate(1525,14216704,104805351,119.5)
        self.assertLess(result['predicted_combined_seconds_with_allowances'],600)
        self.assertEqual(result['original_total_bytes'],119022055)
        self.assertTrue(result['aggregate_evidence_not_synthetic_input_pins'])
        self.assertTrue(result['prediction_is_not_completion_guarantee'])
        with self.assertRaises(ValueError):m.estimate(1525,14216704,104805351,400)
        for count,binary,other,seconds in ((1524,14216704,104805351,119.5),
                (1525,True,104805351,119.5),(1525,14216704,-1,119.5),
                (1525,14216704,104805351,float('nan'))):
            with self.assertRaises(ValueError):m.estimate(count,binary,other,seconds)
