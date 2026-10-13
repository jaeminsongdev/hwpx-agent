import copy
import unittest
import review_pending_r07_closing as v


class PendingReviewTests(unittest.TestCase):
    def setUp(self):
        self.case=dict(state=v.v.CASE_PASS,closing_id=v.STOP['path'])
        self.stop=dict(state='FAILED_NOT_ACCEPTED',error_code='STOP_SUSTAINED_SYSTEM_CPU',
            resource_stop_reason='STOP_SUSTAINED_SYSTEM_CPU',resource_watcher_cleanup_confirmed=True,
            IO=dict(finished=False),actual_test_runtime_executed=False)
        self.plan=dict(accepted_individual_cases=3,remaining_individual_cases=246,
            successful_candidates_requiring_separate_closing=1,remaining_regular_cases=240,
            remaining_corpus_cases=6,next_index=5)
    def test_pending_success_is_not_reexecuted_or_promoted(self):
        actions=v.validate_pending(self.case,self.stop,self.plan)
        self.assertFalse(actions['automatically_reexecute_successful_case004'])
        self.assertFalse(actions['start_case005_before_candidate_closing'])
        self.assertFalse(actions['whole_source_recovery_or_fresh_closing_completed'])
    def test_stop_or_cleanup_drift_is_rejected(self):
        for key,value in (('state',v.v.CLOSING_PASS),('resource_watcher_cleanup_confirmed',False),
                ('resource_stop_reason',None),('actual_test_runtime_executed',True)):
            stop=copy.deepcopy(self.stop);stop[key]=value
            with self.assertRaises(ValueError):v.validate_pending(self.case,stop,self.plan)
    def test_success_or_closing_reference_drift_is_rejected(self):
        for key,value in (('state','STOPPED_NOT_ACCEPTED'),('closing_id','different')):
            case=dict(self.case);case[key]=value
            with self.assertRaises(ValueError):v.validate_pending(case,self.stop,self.plan)
    def test_false_acceptance_or_loss_of_candidate_is_rejected(self):
        for key,value in (('accepted_individual_cases',4),('successful_candidates_requiring_separate_closing',0),
                ('next_index',4),('remaining_individual_cases',245)):
            plan=dict(self.plan);plan[key]=value
            with self.assertRaises(ValueError):v.validate_pending(self.case,self.stop,plan)


if __name__=='__main__':unittest.main()
