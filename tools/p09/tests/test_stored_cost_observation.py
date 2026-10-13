import io
import json
import unittest
from types import SimpleNamespace
from unittest.mock import patch
import stored_cost_observation as s
import run_stored_cost_diagnostic as driver
from test_host_cpu_groups import select


class StoredCostObservationTests(unittest.TestCase):
    def trace(self):
        t=s.CaseTrace(('a','b'));t.feed(b'\nrunning 2 tests\n',0);return t
    def test_chunked_case_start(self):
        t=self.trace();t.feed(b'test a ..',1);self.assertIsNone(t.active)
        t.feed(b'. ',2);self.assertEqual(t.active['case'],'a');self.assertEqual(t.snapshot(3)['active']['observed_wall_seconds'],1)
    def test_complete_original_names_no_assumed_sort(self):
        t=self.trace();t.feed(b'test b ... ok\ntest a ... ok\n',2)
        self.assertEqual([r['case'] for r in t.completed],['b','a']);self.assertIsNone(t.active)
    def test_observed_wall_not_CPU_time(self):
        t=self.trace();t.feed(b'test a ... ',1);t.feed(b'ok\n',5)
        self.assertEqual(t.completed[0]['observed_wall_seconds'],4);self.assertTrue(t.snapshot(5)['observed_times_are_pipe_arrival_wall_times'])
    def test_unknown_case_rejected(self):
        t=self.trace()
        with self.assertRaises(ValueError):t.feed(b'test private_not_allowed ... ok\n',1)
    def test_duplicate_case_rejected(self):
        t=self.trace();t.feed(b'test a ... ok\n',1)
        with self.assertRaises(ValueError):t.feed(b'test a ... ok\n',2)
    def test_concurrent_case_rejected(self):
        t=self.trace();t.feed(b'test a ... \n',1)
        with self.assertRaises(ValueError):t.feed(b'test b ... \n',2)
    def test_fail_and_ignore_are_not_pass(self):
        t=self.trace();t.feed(b'test a ... FAILED\ntest b ... ignored\n',1)
        self.assertEqual([r['result'] for r in t.completed],['FAILED','ignored'])
    def test_wrong_running_count_rejected(self):
        with self.assertRaises(ValueError):s.CaseTrace(('a','b')).feed(b'running 1 tests\n',0)
    def test_private_text_redacted_and_warning_bare_result(self):
        t=self.trace();t.feed(b'test a ... test a has been running for over 60 seconds\n',1)
        t.feed(b'ok\nprivate panic value\ntest result: failed.\n',2);r=t.snapshot(2)
        self.assertEqual(r['completed'][0]['result'],'ok');self.assertNotIn('private panic value',json.dumps(r))
        self.assertFalse(r['raw_test_output_saved']);self.assertTrue(r['summary_seen'])
    def test_pending_line_bound(self):
        t=self.trace()
        with self.assertRaises(ValueError):t.feed(b'x'*4097,1)
    def test_name_scope_bound_and_unique(self):
        for names in ([],('a','a'),('private path',),tuple(str(i) for i in range(250))):
            with self.assertRaises(ValueError):s.CaseTrace(names)
    def test_monotonic_timestamps(self):
        t=self.trace();t.feed(b'test a ... ',2)
        with self.assertRaises(ValueError):t.feed(b'ok\n',1)
    def test_churn_duplicate_group_not_fake_PID_or_CPU(self):
        r=s.churn_summary({'git':[50.,51.]},{'git':frozenset((50,))});s.valid_churn(r)
        item=r['top_changed_groups'][0];self.assertEqual(item['role'],'git');self.assertEqual(item['added_pid_count'],1)
        self.assertEqual(item['removed_pid_count'],0);self.assertIsNone(item['pid']);self.assertTrue(item['cpu_attribution_unavailable'])
    def test_new_group_baseline_unknown_not_zero(self):
        item=s.churn_summary({'private-app':[50.]},{})['top_changed_groups'][0]
        self.assertIsNone(item['added_pid_count']);self.assertIsNone(item['removed_pid_count']);self.assertFalse(item['baseline_known'])
        self.assertEqual(item['role'],'other');self.assertNotIn('private-app',json.dumps(item))
    def test_top4_after_all_groups(self):
        r=s.churn_summary({f'private{i}':[float(50+i)] for i in range(8)},{})
        self.assertEqual(r['changed_group_count'],8);self.assertEqual(r['changed_current_instance_count'],8)
        self.assertEqual(len(r['top_changed_groups']),4);self.assertNotIn('private',json.dumps(r))
    def test_unavailable_identity_not_zero_PID(self):
        r=s.churn_summary({'git':[None],'python':[50.]},{'python':frozenset((50,))})
        self.assertEqual(r['unavailable_identity_group_count'],1);self.assertEqual(r['top_changed_groups'],[])
    def test_churn_extra_fields_and_group_PID_rejected(self):
        r=s.churn_summary({'git':[50.,51.]},{'git':frozenset((50,))});r['top_changed_groups'][0]['cpu']=0
        with self.assertRaises(ValueError):s.valid_churn(r)
        r=s.churn_summary({'git':[50.,51.]},{'git':frozenset((50,))});r['top_changed_groups'][0]['pid']=50
        with self.assertRaises(ValueError):s.valid_churn(r)
    def test_worker_pretty_changes_only_presentation_no_selection(self):
        class Kernel:
            def GetCurrentProcess(self):return 1
            def IsProcessInJob(self,p,j,out):out._obj.value=True;return True
        class Native:
            def __init__(self,*a,**kw):self.warm=True;self.last_churn=s.churn_summary({'x':[50.]},{'x':frozenset((50,))})
            def collect(self,*a):
                if self.warm:self.warm=False;return None
                return select({'x':[16.]},{'x':[50.]})[0]
            def close(self):pass
        process=SimpleNamespace(pid=70,poll=lambda:0);windows=SimpleNamespace(k=Kernel(),processors=16,sample=lambda:{'system_cpu_percent':10.})
        with patch.object(driver.c.sys,'stdin',io.StringIO('P149_GO\n')),patch.object(driver.c,'Windows',return_value=windows), \
                patch.object(driver.c.shutil,'which',return_value='cargo'),patch.object(driver.observation,'ChurnObserver',Native), \
                patch.object(driver.subprocess,'Popen',return_value=process) as called,patch.object(driver.s.time,'sleep'),patch.object(driver.sys,'stderr',io.StringIO()):
            self.assertEqual(driver.worker(driver.task_for(1)),0)
        self.assertEqual(called.call_args.args[0],[str(driver.c.ROOT/driver.s.original.inventory.build.executable_name(1)),
            '--test-threads=1','--format=pretty','--color=never'])
        self.assertEqual(called.call_args.kwargs['env']['RUST_TEST_NOCAPTURE'],'0')
    def test_GO_guard_before_native_and_new_EXE(self):
        class Forbidden:
            def __init__(self,*a,**kw):raise AssertionError('NATIVE_FORBIDDEN')
        with patch.object(driver.c.sys,'stdin',io.StringIO('wrong\n')),patch.object(driver.observation,'ChurnObserver',Forbidden):
            with self.assertRaises(ValueError):driver.worker(driver.task_for(1))
    def test_diagnostic180_not_original1200_and_total_transport_bound(self):
        self.assertEqual(driver.MAXIMUM_SECONDS,180);self.assertEqual(driver.s.original.MAXIMUM_SECONDS,1200)
        self.assertFalse(driver.task_for(1).endswith('tests'))
        self.assertLess(driver.SAVED*(driver.s.MAX_FRAME+driver.CHURN_FRAME)+sum(driver.s.FRAME_BOUNDS[k] for k in ('ready','budget','closed')),32768)
        self.assertEqual(driver.s.MAX_SAVED,10)


if __name__=='__main__':unittest.main()
