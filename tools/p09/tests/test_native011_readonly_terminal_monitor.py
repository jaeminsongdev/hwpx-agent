import json
from types import SimpleNamespace as NS
import unittest
import native011_owned_metadata_audit as original
import native011_current_epoch_owned_audit as failure
import native011_readonly_terminal_monitor as m


def cleaned():
    return dict(exit_code=0,cleanup=True,cleanup_errors=[],owned_job=dict(owned_tree_empty=True,
        cleanup_confirmed=True,job_handle_closed=True,last_job_accounting=dict(active_processes=0,owned_processes=[])))


class Tests(unittest.TestCase):
    def fixture(self):
        guards=[]
        class Guard:
            def __init__(self):
                self.cleanup=False;self.samples=[];self.acquires=0;self.checks=0;self.error=None;self.acquire_error=None
                self.preparation_CPU=NS(summary=lambda:{'Native_policy_changed':False})
            def acquire(self):
                self.acquires+=1
                if self.acquire_error:raise self.acquire_error
            def check(self,**kwargs):
                self.checks+=1
                if self.error:raise self.error
            def close(self):self.cleanup=True
        def factory():guards.append(Guard());return guards[-1]
        Type=m.monitor_type(original.Monitor,original.MARKERS,original.STAGES[:3])
        monitor=Type(factory);monitor.start();process=NS(returncode=None,observe=lambda:None)
        return monitor,guards,process
    def third(self):
        monitor,guards,process=self.fixture()
        # Model positive completed intervals explicitly: Windows monotonic may
        # remain unchanged during these entirely in-memory fixture transitions.
        for count in (1,2,3):
            monitor.started-=.0625
            monitor.accept(list(original.MARKERS[:count]),process)
        monitor.started-=.0625
        return monitor,guards,process

    def test_successful_exit_before_final_marker_has_no_fourth_live_guard(self):
        monitor,guards,process=self.third();before=(monitor.guard,monitor.started)
        process.returncode=0;monitor.accept(list(original.MARKERS),process)
        self.assertEqual((monitor.guard,monitor.started),before);self.assertEqual(len(guards),3)
        self.assertEqual(monitor.seen,3);self.assertTrue(monitor.terminal_observed_after_exit)
        monitor.close();self.assertEqual(len(monitor.records),3)

    def test_live_final_marker_keeps_same_deadline_until_exit_and_cleanup(self):
        monitor,guards,process=self.third();before=(monitor.guard,monitor.started)
        monitor.accept(list(original.MARKERS),process);process.returncode=0
        monitor.accept(list(original.MARKERS),process)
        self.assertEqual((monitor.guard,monitor.started),before);self.assertEqual(len(guards),3)
        self.assertFalse(monitor.terminal_observed_after_exit);monitor.close()

    def test_post_cleanup_audit_guard_is_real_and_distinct_without_phase_credit(self):
        monitor,guards,process=self.third();process.returncode=0;monitor.accept(list(original.MARKERS),process)
        row=cleaned();events=[]
        def cleanup(*args):events.append('actual_cleanup_called')
        proof=m.cleanup_and_audit(process,None,row,monitor,cleanup)
        self.assertEqual(events,['actual_cleanup_called']);self.assertEqual([g.acquires for g in guards],[1,0,0,1])
        self.assertEqual(monitor.seen,3);self.assertFalse(proof['terminal_marker_creates_live_epoch'])
        monitor.terminal_complete(row);monitor.close()
        self.assertEqual([r['stage'] for r in monitor.records],[*original.STAGES[:3],'terminal_audit'])

    def test_failed_child_retains_original_root_error_and_never_starts_audit(self):
        monitor,guards,process=self.third();process.returncode=2
        capture=NS(progress=lambda:(list(original.MARKERS),[]),
            communicate=lambda timeout:(json.dumps(dict(error_code='MODEL_ORIGINAL_CHILD_FAILURE')),''))
        row=dict(owned={})
        with self.assertRaisesRegex(ValueError,'MODEL_ORIGINAL_CHILD_FAILURE'):
            failure.observe_markers(monitor,list(original.MARKERS),process,capture,row,failure.preserve_terminal_failure)
        self.assertTrue(monitor.failed);self.assertEqual(monitor.seen,3);self.assertEqual(len(guards),3)
        self.assertFalse(monitor.post_cleanup_audit_started);monitor.close()

    def test_missing_live_phase_cannot_be_inferred_from_a_successful_exit(self):
        monitor,guards,process=self.fixture();monitor.accept(list(original.MARKERS[:2]),process);process.returncode=0
        with self.assertRaisesRegex(ValueError,'NO_MONITOR_ROTATION_FROM_TERMINAL_PROCESS'):
            monitor.accept(list(original.MARKERS),process)
        self.assertEqual(len(guards),2);self.assertTrue(monitor.failed);monitor.close()

    def test_bad_marker_or_regression_is_sticky(self):
        for bad in (['wrong'],list(original.MARKERS[:2])):
            monitor,guards,process=self.third();monitor.accept(list(original.MARKERS),process)
            with self.assertRaises(ValueError):monitor.accept(bad,process)
            self.assertTrue(monitor.failed);self.assertEqual(len(guards),3);monitor.close()

    def test_original_resource_failure_before_terminal_is_preserved_without_rotation(self):
        monitor,guards,process=self.third();error=ValueError('ORIGINAL_CPU_OR_RAM_STOP');guards[-1].error=error
        with self.assertRaises(ValueError) as caught:monitor.accept(list(original.MARKERS),process)
        self.assertIs(caught.exception,error);self.assertIsNone(monitor.terminal_markers)
        self.assertEqual(len(guards),3);monitor.close()

    def test_audit_requires_all_markers_actual_success_and_known_empty_closed_job(self):
        for bad in ('marker','exit','active','closed'):
            monitor,guards,process=self.third();row=cleaned()
            if bad!='marker':monitor.accept(list(original.MARKERS),process)
            if bad=='exit':row['exit_code']=None
            if bad=='active':row['owned_job']['last_job_accounting']['active_processes']=1
            if bad=='closed':row['owned_job']['job_handle_closed']=False
            with self.assertRaises(ValueError):monitor.start_post_cleanup_audit(row)
            self.assertEqual(len(guards),3);self.assertTrue(monitor.failed);monitor.close()

    def test_post_cleanup_guard_acquisition_failure_not_credited_or_hidden(self):
        monitor,guards,process=self.third();monitor.accept(list(original.MARKERS),process)
        factory=monitor.factory;error=ValueError('ORIGINAL_POST_AUDIT_ADMISSION_STOP')
        def stop():guard=factory();guard.acquire_error=error;return guard
        monitor.factory=stop
        with self.assertRaises(ValueError) as caught:monitor.start_post_cleanup_audit(cleaned())
        self.assertIs(caught.exception,error);self.assertFalse(monitor.post_cleanup_audit_started)
        self.assertTrue(monitor.failed);monitor.close();self.assertTrue(guards[-1].cleanup)

    def test_no_repeated_post_audit_or_child_resumption(self):
        monitor,guards,process=self.third();monitor.accept(list(original.MARKERS),process)
        row=cleaned();monitor.start_post_cleanup_audit(row);count=len(guards)
        with self.assertRaises(ValueError):monitor.start_post_cleanup_audit(row)
        self.assertEqual(len(guards),count);monitor.close()

    def test_expired_live_interval_never_receives_an_audit_guard(self):
        monitor,guards,process=self.third();monitor.started-=600
        monitor.accept(list(original.MARKERS),process)
        with self.assertRaisesRegex(ValueError,'ORIGINAL_THREE_LIVE_DEADLINES'):
            monitor.start_post_cleanup_audit(cleaned())
        self.assertEqual(len(guards),3);self.assertFalse(monitor.post_cleanup_audit_started);monitor.close()

    def test_actual_probe_entry_rejects_any_product_or_go_option_before_windows_setup(self):
        import sys
        from unittest.mock import patch
        with patch.object(sys,'argv',['protocol-fixture','--go']):
            with self.assertRaisesRegex(ValueError,'CLOSED_MARKER_FIXTURE_ONLY_ENTRY'):m.main()
