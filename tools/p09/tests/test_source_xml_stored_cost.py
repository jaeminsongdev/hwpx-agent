import copy
import io
import unittest
from unittest.mock import patch
import run_source_xml_stored_cost as d

class SourceXmlStoredCostTests(unittest.TestCase):
    def test_previous_generation_task_rejected(self):
        with self.assertRaises(ValueError):d.worker(d.old.task_for(3))

    def test_current_r04_lookup_and_adaptive_callback_restored(self):
        before=d.p.b.executable_name(1);current=d.p.b.executable_name(4)
        callback=d.old.s.observed_call;calls=[]
        def invoke(task):
            calls.append((task,d.p.b.executable_name(1),d.old.s.observed_call))
            return 0
        with patch.object(d.old,'worker',side_effect=invoke):self.assertEqual(d.worker(d.old.task_for(4)),0)
        self.assertEqual(calls,[(d.old.task_for(4),current,d.adaptive.observed_call)])
        self.assertEqual(d.p.b.executable_name(1),before);self.assertIs(d.old.s.observed_call,callback)

    def test_unexpected_executable_lookup_denied(self):
        with patch.object(d.old,'worker',side_effect=lambda task:d.p.b.executable_name(2)):
            with self.assertRaises(ValueError):d.worker(d.old.task_for(4))

    def test_diagnostic_does_not_change_original_timeout_or_guards(self):
        self.assertEqual(d.MAXIMUM_SECONDS,360);self.assertEqual(d.old.MAXIMUM_SECONDS,180)
        self.assertEqual(d.full.s.original.MAXIMUM_SECONDS,1200)
        policy=copy.deepcopy(d.p.c.POLICY);callback=d.old.s.Capture;dump=d.old.json.dump
        def invoke(run,destination,*binding):
            self.assertEqual(run,4);self.assertEqual(d.old.MAXIMUM_SECONDS,360)
            self.assertIs(d.old.s.Capture,d.adaptive.Capture)
            row=dict(tests_passed=None,full249_current_qualified=False,signed16_current_qualified=False)
            d.old.json.dump(row,io.StringIO())
            self.assertFalse(row['full249_current_qualified']);self.assertTrue(row['native_cold_periods_explicitly_not_observed'])
            return 1
        with patch.object(d.old,'run_owned',side_effect=invoke):self.assertEqual(d.run_owned('unused',()),1)
        self.assertEqual(d.old.MAXIMUM_SECONDS,180);self.assertEqual(d.p.c.POLICY,policy)
        self.assertIs(d.old.s.Capture,callback);self.assertIs(d.old.json.dump,dump)

    def test_previous_scope_or_runtime_pass_not_accepted_as_parent(self):
        for state in ('PASS_CURRENT_GRAPH_COST_TERMINAL_ACCOUNTED_ONLY_NOT_FULL249_OR_GATE',
                'PASS_CURRENT_GRAPH_FULL_STOP_ACCOUNTED_ONLY_NOT_RUNTIME_OR_GATE',
                'PASS_CURRENT_ADAPTIVE_SOURCE_XML_FULL249_CLOSING_ONLY_NOT_SQL_NATIVE_PRODUCT_OR_GATE'):
            with self.assertRaises((ValueError,KeyError)):d.parent_scope(dict(state=state))

    def test_parent_receipt_is_current_actual_stop_not_future_or_raw_pass(self):
        self.assertEqual(d.PARENT['path'],
            'implementation/p09/evidence/p09-165-adaptive-source-xml-full.terminal-audit-run01.v1.json')
        self.assertEqual(d.PARENT['bytes'],386991)
        self.assertEqual(d.PARENT['sha256'],'319ee52b7251ed48272c409daebe4b3470a6803b5aeb1d7cdbd92024c4124eb1')

    def test_adaptive_and_case_collectors_keep_original_bounds(self):
        self.assertEqual(d.old.SAVED,6);self.assertEqual(d.old.CHURN_FRAME,1400)
        self.assertEqual(d.adaptive.FOOTER_LIMIT,512)
        self.assertEqual(d.old.s.MAX_FRAME,2800)

if __name__=='__main__':unittest.main()
