"""New measured cold-sample interval models; no sampler/Native is run."""
from types import SimpleNamespace as NS
import unittest
import native011_owned_metadata_audit as runner


class ColdSampleContracts(unittest.TestCase):
    def test_measured_half_second_without_mutating_baseline_or_adding_samples(self):
        now=[10.0];slept=[];guard=NS(samples=[],cpu=2.0,last=10.0)
        monitor=runner.Monitor(lambda:guard);monitor.guard=guard
        def sleep(value):slept.append(value);now[0]+=value
        monitor.cold_sample_interval(clock=lambda:now[0],sleep=sleep)
        self.assertGreaterEqual(now[0],10.5);self.assertLessEqual(now[0],10.55)
        self.assertEqual((guard.last,guard.cpu,guard.samples),(10.0,2.0,[]))
        self.assertTrue(all(0<v<=.05 for v in slept))
    def test_existing_sample_is_not_delayed_or_rewritten(self):
        guard=NS(samples=[{'original':True}],cpu=2.0,last=10.0)
        monitor=runner.Monitor(lambda:guard);monitor.guard=guard
        monitor.cold_sample_interval(clock=lambda:10.0,sleep=lambda _:self.fail('unexpected sleep'))
        self.assertEqual(guard.samples,[{'original':True}])
    def test_unseeded_original_guard_does_not_need_an_artificial_baseline(self):
        guard=NS(samples=[],cpu=None,last=0)
        monitor=runner.Monitor(lambda:guard);monitor.guard=guard
        monitor.cold_sample_interval(clock=lambda:0,sleep=lambda _:self.fail('unexpected sleep'))
        self.assertIsNone(guard.cpu)
    def test_frozen_clock_is_bounded_instead_of_busy_looping(self):
        guard=NS(samples=[],cpu=2.0,last=10.0);calls=[]
        monitor=runner.Monitor(lambda:guard);monitor.guard=guard
        with self.assertRaisesRegex(ValueError,'COLD_SAMPLE_CLOCK_DID_NOT_ADVANCE'):
            monitor.cold_sample_interval(clock=lambda:10.0,sleep=lambda value:calls.append(value))
        self.assertEqual(len(calls),16)


if __name__=='__main__':unittest.main()
