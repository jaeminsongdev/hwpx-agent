import json
import unittest
from types import SimpleNamespace as NS
from unittest.mock import patch
import preparation_live_cpu_observer_v1 as p


def sample(cpu,created=1):
    return dict(rows={10:(created,cpu,"python.exe"),20:(2,cpu//2,"python.exe")},system=(cpu,100+cpu*2,100+cpu),scan_seconds=.01)


class Tests(unittest.TestCase):
    def test_typed_closed_target_and_no_self(self):
        value=dict(pid=10,creation_time_100ns=123)
        self.assertEqual(p.target_request(json.dumps(value),20),value)
        for row in ({**value,"pid":True},{**value,"pid":20},{**value,"creation_time_100ns":0},{**value,"command":"forbidden"}):
            with self.assertRaises(ValueError):p.target_request(json.dumps(row),20)

    def test_target_input_is_bounded(self):
        for value in (None,"","x"*129):
            with self.assertRaises(ValueError):p.target_request(value,20)

    def test_process_share_missing_reuse_and_counter_reset_not_zero(self):
        a=sample(1);b=sample(3)
        self.assertEqual(p.share(a,b,10),round(100/3,6))
        self.assertIsNone(p.share(a,b,99))
        self.assertIsNone(p.share(a,sample(3,2),10))
        b["rows"][10]=(1,0,"python.exe");self.assertIsNone(p.share(a,b,10))

    def test_fixed_unavailable_is_missing_not_zero(self):
        groups=dict(system_cpu_percent=99,top_cpu_groups=[],inaccessible_processes=10,newly_seen_or_reused_PIDs=1,scan_seconds=.01)
        result=p.compact(sample(1),sample(3),groups,dict(available=False,values=None),10,20,1)
        self.assertIsNone(result["Defender_CPU"]);self.assertFalse(result["fixed_counter_available"])
        self.assertEqual(result["system_CPU"],99)

    def test_fixed_unstable_pid_is_missing(self):
        groups=dict(system_cpu_percent=90,top_cpu_groups=[],inaccessible_processes=0,newly_seen_or_reused_PIDs=0,scan_seconds=.01)
        fixed=dict(available=True,values=dict(MsMpEng=dict(pid_stable=False,machine_cpu_percent=99)))
        self.assertIsNone(p.compact(sample(1),sample(3),groups,fixed,10,20,1)["Defender_CPU"])

    def test_terminal_target_does_not_sample_or_signal_it(self):
        probe=NS(sample=lambda:(_ for _ in ()).throw(AssertionError("NO_SAMPLE")))
        result=p.watch(lambda:False,lambda:sample(1),None,probe,10,20)
        self.assertTrue(result["target_terminal_observed"]);self.assertEqual(result["samples"],[])

    def test_sample_bound_and_original_target_not_terminated(self):
        clock=[0.];count=[0]
        def snapshot():count[0]+=1;return sample(count[0])
        def pause(value):clock[0]+=value
        groups=dict(system_cpu_percent=90,top_cpu_groups=[],inaccessible_processes=0,newly_seen_or_reused_PIDs=0,scan_seconds=.01)
        with patch.object(p,"MAX_SAMPLES",2):
            result=p.watch(lambda:True,snapshot,lambda *a:groups,NS(sample=lambda:dict(available=False,values=None)),10,20,clock=lambda:clock[0],pause=pause)
        self.assertEqual(result["sample_count"],2);self.assertEqual(result["stop_reason"],"OBSERVATION_BOUND_REACHED")
        self.assertFalse(result["target_terminal_observed"])

    def test_observer_cost_bound_does_not_claim_complete_coverage(self):
        clock=[0.]
        def pause(value):clock[0]+=value
        with patch.object(p,"MAX_OBSERVER_WORK_SECONDS",.001):
            result=p.watch(lambda:True,lambda:sample(1),None,NS(sample=lambda:dict(available=False)),10,20,clock=lambda:clock[0],pause=pause)
        self.assertEqual(result["stop_reason"],"OBSERVER_WORK_BUDGET_REACHED")
        self.assertEqual(result["sample_count"],0)

    def test_exception_text_does_not_leak_paths_or_commands(self):
        self.assertEqual(p.error_code(ValueError("C:\\private\\token value")),"ValueError")
        self.assertEqual(p.error_code(ValueError("BOUNDED_DIAGNOSTIC_FAILURE")),"BOUNDED_DIAGNOSTIC_FAILURE")

    def test_sampling_failure_preserves_already_collected_evidence(self):
        clock=[0.];calls=[0]
        def snapshot():
            calls[0]+=1
            if calls[0]>2:raise ValueError("BOUNDED_PROCESS_SCAN_FAILURE")
            return sample(calls[0])
        def pause(value):clock[0]+=value
        groups=dict(system_cpu_percent=90,top_cpu_groups=[],inaccessible_processes=0,newly_seen_or_reused_PIDs=0,scan_seconds=.01)
        result=p.watch(lambda:True,snapshot,lambda *a:groups,NS(sample=lambda:dict(available=False)),10,20,clock=lambda:clock[0],pause=pause)
        self.assertEqual(result["sample_count"],1);self.assertEqual(result["stop_reason"],"SAMPLING_FAILURE")
        self.assertEqual(result["observer_error"],"BOUNDED_PROCESS_SCAN_FAILURE")

    def test_partial_constructor_query_is_closed_and_not_retried(self):
        closed=[];api=p.TrackedPDH(NS(open=lambda:(0,42),close=lambda h:closed.append(h) or 0))
        self.assertEqual(api.open(),(0,42));self.assertTrue(api.close_partial());self.assertTrue(api.close_partial())
        self.assertEqual(closed,[42])
