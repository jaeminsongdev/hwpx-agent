import unittest
import owned_cpu_baseline_v1 as MODULE


class Original:
    def __init__(self):self.cpu=None;self.last=0.;self.samples=[];self.deadline=600;self.hot=0;self.cleanup=False
    def check(self):return self.last,self.cpu
    def close(self):self.cleanup=True


class Tests(unittest.TestCase):
    def test_real_clock_values_seed_epoch_without_replacing_original_guard_methods(self):
        stamps=iter((100.,100.000001))
        cls=MODULE.guard_type(Original,wall=lambda:next(stamps),cpu=lambda:10.)
        guard=cls();self.assertEqual(guard.check(),(100.,10.))
        self.assertIs(cls.check,Original.check);self.assertIs(cls.close,Original.close)
        self.assertEqual((guard.deadline,guard.hot,guard.samples),(600,0,[]))
        self.assertEqual(Original().check(),(0.,None));guard.close();self.assertTrue(guard.cleanup)

    def test_active_owner_invalid_clock_or_slow_epoch_cannot_be_seeded(self):
        class Active(Original):
            def __init__(self):super().__init__();self.cpu=1.
        with self.assertRaises(ValueError):MODULE.guard_type(Active)()
        for stamps,cpu in (((100.,100.1),1.),((100.,99.),1.),((True,1.),1.),((100.,100.),float("nan")),((100.,100.),-1.)):
            values=iter(stamps)
            with self.assertRaises(ValueError):MODULE.guard_type(Original,wall=lambda:next(values),cpu=lambda:cpu)()

    def test_first_ratio_uses_counter_delta_not_fabricated_zero_or_a_new_sample(self):
        values=iter((100.,100.))
        guard=MODULE.guard_type(Original,wall=lambda:next(values),cpu=lambda:10.)()
        measured_first=100*(10.05-guard.cpu)/(100.5-guard.last)/16
        self.assertAlmostEqual(measured_first,.625)
        self.assertEqual(guard.samples,[]);self.assertEqual(guard.owned_CPU_baseline["original_samples_added"],0)
