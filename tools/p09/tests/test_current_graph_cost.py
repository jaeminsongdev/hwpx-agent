import copy
import io
import unittest
from types import SimpleNamespace
from unittest.mock import patch
import run_current_graph_cost as d

class CurrentGraphCostTests(unittest.TestCase):
    def test_stale_task_rejected_before_launch(self):
        with self.assertRaises(ValueError):d.worker(d.old.task_for(1))

    def test_current_r03_lookup_restored_and_all249_presentation_only(self):
        before=d.p.b.executable_name(1);current=d.p.b.executable_name(3);calls=[]
        def worker(task):
            calls.append((task,d.p.b.executable_name(1)));return 0
        with patch.object(d.old,'worker',side_effect=worker):self.assertEqual(d.worker(d.old.task_for(3)),0)
        self.assertEqual(calls,[(d.old.task_for(3),current)]);self.assertEqual(d.p.b.executable_name(1),before)

    def test_unexpected_lookup_rejected(self):
        def worker(task):return d.p.b.executable_name(2)
        with patch.object(d.old,'worker',side_effect=worker):
            with self.assertRaises(ValueError):d.worker(d.old.task_for(3))

    def test_diagnostic360_does_not_change_qualification1200_or_original180(self):
        self.assertEqual(d.MAXIMUM_SECONDS,360);self.assertEqual(d.old.MAXIMUM_SECONDS,180)
        self.assertEqual(d.full.s.original.MAXIMUM_SECONDS,1200)
        before=copy.deepcopy(d.p.c.POLICY);dump=d.old.json.dump
        def invoke(run,destination,*binding):
            self.assertEqual(run,3);self.assertEqual(d.old.MAXIMUM_SECONDS,360)
            row={'tests_passed':None,'full249_current_qualified':False,'signed16_current_qualified':False}
            d.old.json.dump(row,io.StringIO());return 1
        with patch.object(d.old,'run_owned',side_effect=invoke):self.assertEqual(d.run_owned('unused',()),1)
        self.assertEqual(d.old.json.dump,dump);self.assertEqual(d.old.MAXIMUM_SECONDS,180)
        self.assertEqual(d.p.c.POLICY,before)

    def test_partial_stop_is_not_fullpass_or_stale_authority(self):
        for state in ('PASS_UNFILTERED_COST_DIAGNOSTIC_TERMINAL_ACCOUNTED_NOT_FULL249_OR_GATE','PASS_CURRENT_GRAPH_FULL249_CLOSING_ONLY_NOT_SQL_NATIVE_PRODUCT_OR_GATE'):
            with self.assertRaises((ValueError,KeyError)):d.parent_scope(dict(state=state))

if __name__=='__main__':unittest.main()
