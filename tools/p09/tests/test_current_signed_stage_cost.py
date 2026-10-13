import copy
import threading
import unittest
from unittest.mock import patch
import run_current_signed_stage_cost as d

class CurrentSignedStageCostTests(unittest.TestCase):
    def text(self,count=None):
        return ''.join(f'P149_SIGNED_COST:0:{s}:1\n' for s in d.stage.ORDER[:count])

    def capture(self,stdout=b'',stderr=b''):
        cap=object.__new__(d.StageCapture);cap.lock=threading.Lock()
        cap.buffers={'stdout':bytearray(stdout),'stderr':bytearray(stderr)}
        cap.error=None;cap.output_limit=32768;return cap

    def test_stale_task_denied_before_delegate(self):
        with self.assertRaises(ValueError):d.worker(d.prior.old.task_for(4))

    def test_selected_argv_is_exact_single_current_case(self):
        exe=d.c.ROOT/d.p.b.executable_name(4)
        self.assertEqual(d.profile_argv(exe),[str(exe),d.NAME,'--exact','--test-threads=1','--nocapture','--format=terse'])

    def test_original_job_worker_and_r04_redirect_kept(self):
        calls=[];old_name=d.p.b.executable_name(1)
        def invoke(task):
            calls.append((task,d.p.b.executable_name(1)))
            return 0
        with patch.object(d.original,'worker',side_effect=invoke):self.assertEqual(d.worker(d.TASK),0)
        self.assertEqual(calls,[(d.original.task_for(4),d.p.b.executable_name(4))])
        self.assertEqual(d.p.b.executable_name(1),old_name)

    def test_diagnostic180_never_changes_full1200_or_policy(self):
        before=copy.deepcopy(d.c.POLICY)
        self.assertEqual(d.MAXIMUM_SECONDS,180);self.assertEqual(d.original.MAXIMUM_SECONDS,1200)
        self.assertEqual(d.c.POLICY,before)

    def test_previous_raw_or_fullpass_not_parent(self):
        for state in ('PASS_CURRENT_GRAPH_COST_TERMINAL_ACCOUNTED_ONLY_NOT_FULL249_OR_GATE',
                'PASS_CURRENT_ADAPTIVE_SOURCE_XML_FULL249_CLOSING_ONLY_NOT_SQL_NATIVE_PRODUCT_OR_GATE'):
            with self.assertRaises((ValueError,KeyError)):d.parent_scope(dict(state=state))

    def test_partial_marker_no_runtime_or_case_promotion(self):
        cap=self.capture(stderr=('private unrelated line\n'+self.text(7)).encode())
        row=cap.diagnostic();self.assertFalse(row['signed_stage_cost']['signed16_runtime_complete'])
        self.assertEqual(row['signed_stage_cost']['fully_observed_case_sequences'],0)
        self.assertFalse(cap.selected_finished());self.assertNotIn('private',str(row))

    def test_duplicate_or_foreign_stage_rejected(self):
        for text in (self.text(2)+self.text(1),'P149_SIGNED_COST:0:untrusted_stage:1\n'):
            with self.assertRaises(ValueError):self.capture(stderr=text.encode()).cost()

    def test_finished_requires_all16_sequences_and_exact_filtered_summary(self):
        body=''.join(self.text().replace('P149_SIGNED_COST:0:',f'P149_SIGNED_COST:{i}:') for i in range(16))
        good=b'test result: ok. 1 passed; 0 failed; 0 ignored; 0 measured; 248 filtered out;\n'
        cap=self.capture(stdout=good,stderr=body.encode());self.assertTrue(cap.selected_finished())
        self.assertFalse(cap.cost()['signed16_runtime_complete'])
        for bad in (good.replace(b'248',b'247'),good+good,good.replace(b'0 ignored',b'1 ignored')):
            self.assertFalse(self.capture(stdout=bad,stderr=body.encode()).selected_finished())

if __name__=='__main__':unittest.main()
