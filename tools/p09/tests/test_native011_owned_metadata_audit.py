"""Phase-monitor protocol and exact source bootstrap models, no process."""
from pathlib import Path
from types import SimpleNamespace as NS
import unittest
import native011_owned_metadata_audit as runner
import native011_metadata_audit as audit
import native011_metadata_epochs as epochs


class MonitorContracts(unittest.TestCase):
    def fixture(self):
        guards=[]
        class Guard:
            def __init__(self):
                self.cleanup=False;self.samples=[];self.acquires=0;self.error=None
                self.preparation_CPU=NS(summary=lambda:{'Native_policy_changed':False})
            def acquire(self):self.acquires+=1
            def check(self,**kwargs):
                if self.error:raise self.error
            def close(self):self.cleanup=True
        def factory():guards.append(Guard());return guards[-1]
        monitor=runner.Monitor(factory);monitor.start();owned=NS(returncode=None,observe=lambda:None)
        return monitor,guards,owned
    def test_exact_four_markers_with_fresh_guards_no_child_mutex_takeover(self):
        monitor,guards,owned=self.fixture();monitor.accept(list(runner.MARKERS),owned);monitor.close()
        self.assertEqual(monitor.seen,4);self.assertEqual(len(guards),4)
        self.assertEqual([g.acquires for g in guards],[1,0,0,0])
        self.assertTrue(all(g.cleanup for g in guards))
    def test_reobserving_same_prefix_does_not_reset_a_timer(self):
        monitor,guards,owned=self.fixture()
        monitor.accept([runner.MARKERS[0]],owned);monitor.accept([runner.MARKERS[0]],owned)
        self.assertEqual(len(guards),1);monitor.close()
    def test_bad_marker_order_is_sticky(self):
        monitor,guards,owned=self.fixture()
        with self.assertRaises(ValueError):monitor.accept([runner.MARKERS[1]],owned)
        with self.assertRaises(ValueError):monitor.accept([runner.MARKERS[0]],owned)
        self.assertTrue(monitor.failed);self.assertEqual(len(guards),1);monitor.close()
    def test_terminal_child_cannot_supply_a_new_phase(self):
        monitor,guards,owned=self.fixture();monitor.accept([runner.MARKERS[0]],owned);owned.returncode=0
        with self.assertRaisesRegex(ValueError,'NO_MONITOR_ROTATION_FROM_TERMINAL_PROCESS'):
            monitor.accept(list(runner.MARKERS[:2]),owned)
        self.assertEqual(len(guards),1);monitor.close()
    def test_first_resource_failure_is_not_replaced_and_no_new_guard_created(self):
        monitor,guards,owned=self.fixture();original=ValueError('ORIGINAL_RAM_STOP');guards[0].error=original
        with self.assertRaises(ValueError) as caught:monitor.accept(list(runner.MARKERS[:2]),owned)
        self.assertIs(caught.exception,original);self.assertEqual(len(guards),1)
        with self.assertRaises(ValueError):monitor.check()
        monitor.close()
    def test_child_parent_protocol_and_exact_construction_source_match(self):
        self.assertEqual(runner.STAGES,epochs.STAGES);self.assertEqual(runner.MARKERS,epochs.MARKERS)
        root=Path(__file__).resolve().parents[3];plan=audit.bootstrap(root)
        self.assertTrue(callable(plan.construct));self.assertEqual(plan.SELF,'tools/p09/native011_parent_plan.py')


if __name__=='__main__':unittest.main()
