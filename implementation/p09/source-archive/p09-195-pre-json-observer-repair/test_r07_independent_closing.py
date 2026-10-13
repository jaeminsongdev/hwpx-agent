import copy
import contextlib
import io
import types
import unittest
from unittest.mock import Mock,patch
import recover_r07_case004_closing as r


class IndependentClosingTests(unittest.TestCase):
    def test_rates_lower_binary_only_and_preserve_original_pacer(self):
        p=r.Pacer();p.select('known.exe');self.assertEqual(p.rate,1572864)
        p.select('known.json');self.assertEqual(p.rate,4194304)
        self.assertIsInstance(p,r.weighted.WeightedPacer);self.assertEqual(p.tokens,65536)
    def test_original_policy_and_deadline_not_extended(self):
        self.assertEqual(r.c.POLICY['emergency_cpu_percent'],98)
        self.assertEqual(r.c.POLICY['emergency_cpu_consecutive_samples'],4)
        self.assertEqual(r.b.run.pressure.observation.weighted.LiveSQLReader.__init__.__globals__['MAX_SCOPE_SECONDS'],600)
    def test_rate_budget_refuses_impossible_size(self):
        with self.assertRaises(ValueError):r.estimate({'large.exe':dict(bytes=1000*1024*1024)})
    def test_rate_budget_does_not_claim_guaranteed_finish(self):
        row=r.estimate({'small.exe':dict(bytes=1),'other':dict(bytes=2)})
        self.assertTrue(row['prediction_is_not_completion_guarantee'])
        self.assertLess(row['estimated_seconds_with_metadata_allowance_and_margin'],600)
    def test_failed_path_redirects_only_fresh_output(self):
        with patch.object(r,'RAW_SCOPE',return_value='fresh') as scoped:
            self.assertEqual(r.redirect(r.STOP['path'],'new',fresh=True),'fresh')
            scoped.assert_called_once_with('new',fresh=True)
    def test_original_failed_input_path_not_redirected(self):
        with patch.object(r,'RAW_SCOPE',return_value='original') as scoped:
            r.redirect(r.STOP['path'],'new',fresh=False)
            scoped.assert_called_once_with(r.STOP['path'],fresh=False)
    def test_readonly_alias_cannot_be_injected_twice(self):
        with self.assertRaises(ValueError):r.progress(None,[],{},None,'unused',extra=((r.STOP['path'],{}),))
    def test_unqualified_recovery_rejected_before_original_acceptance(self):
        with patch.object(r.v,'accept_case',side_effect=AssertionError('NO_ACCEPT')):
            with self.assertRaises(ValueError):r.validate_recovery({}, {},{},[],{})
    def test_missing_controller_sources_rejected(self):
        doc=dict(recovery_publisher='P195_independent_closing',original_failed_closing_reference=r.STOP['path'],
            original_failed_closing_pin=r.STOP,candidate_case_pin=r.CASE,candidate_body_reexecuted=False,
            additional_product_child_executed=False,original_failed_file_not_replaced=True,
            IO=dict(finished=True,bound_inputs=10,final_fresh_hashes=10,maximum_scope_seconds=600,
                read_rates_by_kind=dict(binary=1572864,other=4194304)),
            accepted_new_case_count=1,whole_original68_EXE_and_Rust785_closed=True,recovery_controller_input_pins=[])
        with self.assertRaises(ValueError):r.validate_recovery(doc,{}, {},[],{})
        failed=dict(state='FAILED_NOT_ACCEPTED')
        r.attach(failed,[],[])
        self.assertEqual(failed['state'],'FAILED_NOT_ACCEPTED')
        self.assertIsNone(failed['recovery_metadata_observation'])
        self.assertEqual(failed['recovery_controller_input_pins'],[])
    def test_existing_fixture_reader_unchanged(self):
        fixture=object();actual=object()
        with patch.object(r,'RAW_READER',return_value='fixture') as original,patch.object(r,'Reader') as observed:
            self.assertEqual(r.factory(fixture,None,[actual],[],protected=('known.exe',)),'fixture')
            original.assert_called_once_with(fixture,protected=('known.exe',));observed.assert_not_called()
    def test_same_whole_scope_and_actual_reader_single_owner(self):
        owner=object();readers=[]
        with patch.object(r,'Reader',return_value='actual') as observed:
            self.assertEqual(r.factory(owner,'context',[owner],readers),'actual')
            observed.assert_called_once_with(owner,'context');self.assertEqual(readers,['actual'])
            with self.assertRaises(ValueError):r.factory(owner,'context',[owner],readers)
    def test_recovery_does_not_call_case_body_and_restores_roles(self):
        before=(r.b.s.scoped_path,r.b.run.pressure.PressureReader,r.b.contracts,r.json.dump)
        with patch.object(r,'RAW_SCOPE',return_value='fresh'),patch.object(r.b,'close',return_value=2) as closing, \
                patch.object(r.core,'run_case',side_effect=AssertionError('NO_REEXECUTION')):
            self.assertEqual(r.recover(1),2);closing.assert_called_once_with(5)
        self.assertEqual(before,(r.b.s.scoped_path,r.b.run.pressure.PressureReader,r.b.contracts,r.json.dump))


if __name__=='__main__':unittest.main()
