import copy
import io
import unittest
from types import SimpleNamespace
from unittest.mock import patch
import build_observed_graph_product as s


class ObservedGraphBuildTests(unittest.TestCase):
    def pump(self,host=10,result=None):
        records=[];clock=[0.0];process=SimpleNamespace(pid=222,poll=lambda:result,stdout='pipe')
        observer=SimpleNamespace(collect=lambda owned:dict(stable_candidate_count=1));windows=SimpleNamespace(processors=16,sample=lambda:dict(system_cpu_percent=host))
        pump=s.Pump(process,observer,windows,111,clock=lambda:clock[0],emit=records.append)
        return pump,records,clock

    def test_first_native_sample_is_not_fabricated(self):
        pump,records,clock=self.pump();pump.poll();self.assertEqual(len(records),1)
        clock[0]=1;pump.poll();self.assertEqual(records[-1]['kind'],'sample');self.assertEqual(pump.total,1)

    def test_initial_two_samples_saved(self):
        pump,records,clock=self.pump()
        for n in range(1,4):clock[0]=n;pump.poll()
        self.assertEqual(pump.total,3);self.assertEqual(pump.saved,2)

    def test_hot_samples_are_finite_and_budget_explicit(self):
        pump,records,clock=self.pump(host=99)
        for n in range(1,13):clock[0]=n;pump.poll()
        pump.closing();self.assertEqual(pump.saved,10);self.assertEqual(pump.unsaved,2)
        self.assertEqual(sum(r['kind']=='budget' for r in records),1);self.assertTrue(records[-1]['diagnostic_budget_limited'])

    def test_terminal_poll_collects_real_final_sample(self):
        pump,records,clock=self.pump(result=0);self.assertEqual(pump.poll(),0);self.assertEqual(pump.saved,1)

    def test_process_interface_is_not_replaced(self):
        pump,_,_=self.pump();self.assertEqual(pump.stdout,'pipe');self.assertEqual(pump.pid,222)

    def test_fresh_r03_must_not_overlap_history(self):
        with self.assertRaises(ValueError):s.fresh_scope({s.p.b.executable_name(3):{}})
        with patch.object(s.p.s,'scoped_path',return_value=SimpleNamespace()):self.assertTrue(s.fresh_scope({}).endswith('p152-r03.exe'))

    def test_wrong_worker_task_denied_before_child(self):
        with self.assertRaises(ValueError):s.worker(s.p.b.task_for(2))

    def test_original_compile_recipe_and_policy_unchanged(self):
        before=copy.deepcopy(s.p.c.POLICY);r=s.p.s.recipe(s.RUN)
        self.assertEqual(r['compile_maximum_seconds'],600);self.assertEqual(r['full249_maximum_seconds'],1200)
        self.assertEqual(len(r['test_package_profile_config']),81);self.assertEqual(s.p.c.POLICY,before)

    def test_original_frame_budget_under32768(self):
        bound=s.observed.FRAME_BOUNDS
        self.assertEqual(sum((bound['ready'],10*bound['sample'],bound['budget'],bound['closed'])),28896)
        self.assertLess(28896,32768)

    def test_build_capture_uses_original_bounded_pipe_not_full249_parser(self):
        fake=SimpleNamespace(process=SimpleNamespace(returncode=0),observer_closed=True,observer_error=None,observer_pending=b'',records=[dict(kind='sample')])
        with patch.object(s.RAW_CAPTURE,'communicate',return_value=('Cargo-proof','native-frames')):
            self.assertEqual(s.DiagnosticCapture.communicate(fake,1),('Cargo-proof','native-frames'))
        fake.observer_closed=False
        with patch.object(s.RAW_CAPTURE,'communicate',return_value=('Cargo-proof','')):
            with self.assertRaises(ValueError):s.DiagnosticCapture.communicate(fake,1)


if __name__=='__main__':unittest.main()
