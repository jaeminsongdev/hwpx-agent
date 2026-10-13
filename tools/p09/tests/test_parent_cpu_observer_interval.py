import unittest
import pre_go_parent_cpu_observer_r2 as d

class ParentIntervalTests(unittest.TestCase):
    def test_each_counter_window_fresh_not_cached_or_duplicate(self):
        now=[0.0];sleeps=[]
        def sleep(delta):sleeps.append(delta);now[0]+=delta
        gate=d.FreshInterval(clock=lambda:now[0],sleep=sleep)
        for _ in range(4):gate.wait();gate.completed()
        self.assertEqual(now[0],2.0);self.assertEqual(sleeps,[0.5]*4)
        self.assertEqual(d.prior.c.POLICY['emergency_cpu_consecutive_samples'],4)
    def test_clock_stall_or_reset_cannot_turn_zero_interval_into_success(self):
        gate=d.FreshInterval(clock=lambda:0.0,sleep=lambda _:None)
        with self.assertRaises(ValueError):gate.wait()
        now=[1.0];gate=d.FreshInterval(clock=lambda:now[0],sleep=lambda _:None);now[0]=0
        with self.assertRaises(ValueError):gate.wait()

if __name__=='__main__':unittest.main()
