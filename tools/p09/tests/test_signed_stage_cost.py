import copy
import unittest
from unittest.mock import patch

import run_signed_stage_cost as subject


class SignedStageCostTests(unittest.TestCase):
    def text(self,index=0,count=None):
        return ''.join(f'P149_SIGNED_COST:{index}:{stage}:{n+1}\n' for n,stage in enumerate(subject.ORDER[:count]))

    def test_full16_sequences_are_observation_only_until_original_runtime_pass(self):
        row=subject.observe_cost(''.join(self.text(n) for n in range(16)))
        self.assertEqual(row['fully_observed_case_sequences'],16)
        self.assertFalse(row['signed16_runtime_complete'])
        self.assertTrue(row['outer_signed_pair_overlaps_nested_PAIR_do_not_sum_both'])

    def test_partial_prefix_retains_only_completed_markers_not_future_or_case_pass(self):
        row=subject.observe_cost(self.text(0,7))
        self.assertEqual(row['next_expected_stage'],subject.ORDER[7])
        self.assertEqual(row['fully_observed_case_sequences'],0)
        self.assertFalse(row['signed16_runtime_complete'])

    def test_duplicate_wrong_order_index_backwards_and_incomplete_predecessor_rejected(self):
        for text in (self.text(0,2)+self.text(0,1),self.text(0,2)+self.text(1,1),self.text(1)+self.text(0),self.text(0).replace('numeric_derivative','changed_setup')):
            with self.assertRaises(ValueError): subject.observe_cost(text)

    def test_closed_marker_range_and_event_budget(self):
        for text in ('P149_SIGNED_COST:36:original_expected:1\n','P149_SIGNED_COST:0:private_value:1\n','P149_SIGNED_COST:0:original_expected:180000001\n','P149_SIGNED_COST:token\n',' '*32769,''.join(self.text(i) for i in range(17))):
            with self.assertRaises(ValueError): subject.observe_cost(text)

    def test_private_unrelated_output_and_incomplete_marker_not_persisted_as_events(self):
        row=subject.observe_cost('unrelated private line\n'+self.text(0,1)+'P149_SIGNED_COST:0:numeric_derivative:')
        self.assertEqual(len(row['events']),1)
        self.assertNotIn('private',str(row))

    def test_exact_cfg_removal_preserves_original_assertion_text(self):
        for name,stages in ((subject.SOURCE,subject.OUTER),(subject.CONSUMER,subject.PAIR)):
            indent='        ' if name==subject.SOURCE else '    '
            statements=(*subject.INITIAL[name],*(f'timer.record("{stage}");' for stage in stages))
            source=('use super::*;\n'+subject.MODULE if name==subject.SOURCE else 'use super::*;\n')
            source+=''.join(indent+'#[cfg(test)]\n'+indent+statement+'\n' for statement in statements)+'assert_original();\n'
            self.assertEqual(subject.body_view(source,name),'use super::*;\nassert_original();\n')
            with self.assertRaises(ValueError): subject.body_view(source.replace('#[cfg(test)]','#[cfg(any())]',1),name)

    def test_original_worker_keeps_exact_filter_thread_GO_and_only_profile_nocapture(self):
        from tests.test_stored_signed_continuation import StoredSignedContinuationTests
        helper=StoredSignedContinuationTests()
        real=subject.original.run_worker
        for task in (subject.INVENTORY,subject.PROFILE):
            def call_original(t):
                # The existing guard exercises the real original waiting worker.
                return real(t)
            with patch.object(subject.original,'run_worker',side_effect=call_original):
                # Fake parent boundary observes only the explicitly added flag;
                # source original waiting-worker contract was verified by r10.
                captured=[]
                def boundary(t):
                    args=['cargo','--',subject.original.NAME,'--exact','--test-threads=1'] if t==subject.PROFILE else ['cargo','--','--list','--format','terse']
                    return subject.subprocess.call(args,stdin=subject.subprocess.DEVNULL)
                with patch.object(subject.original,'run_worker',side_effect=boundary),patch.object(subject.subprocess,'call',side_effect=lambda a,**k:captured.append(a) or 0):
                    self.assertEqual(subject.run_worker(task),0)
                self.assertEqual('--nocapture' in captured[0],task==subject.PROFILE)
                if task==subject.PROFILE: self.assertEqual(captured[0][-1],'--test-threads=1')
        self.assertEqual(helper.worker(subject.original.CHANGED)[0],0)

    def test_short_finite_duration_does_not_expand600_or_parent_limits(self):
        before=copy.deepcopy(subject.maintenance.POLICY)
        for task in (subject.INVENTORY,subject.PROFILE):
            subject.require_duration(task,180)
            for bad in (True,29,181,600):
                with self.assertRaises(ValueError): subject.require_duration(task,bad)
        self.assertEqual(subject.maintenance.POLICY,before)

    def test_inventory_reference_requires_explicit_run(self):
        self.assertTrue(subject.inventory_path(1).endswith('inventory-run01.v1.json'))
        for bad in (0,100,True,'latest'):
            with self.assertRaises(ValueError): subject.inventory_path(bad)

    def test_empty_observation_never_invents_pending_stage_or_complete_cases(self):
        row=subject.observe_cost('')
        self.assertEqual(row['events'],[])
        self.assertEqual(row['fully_observed_case_sequences'],0)
        self.assertIsNone(row['next_expected_stage'])
