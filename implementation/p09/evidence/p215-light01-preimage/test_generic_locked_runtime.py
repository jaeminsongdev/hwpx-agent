import copy
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import resume_generic_locked_runtime as g
FIXTURES=None


class GenericTests(unittest.TestCase):
    def setUp(self):
        if FIXTURES is None:raise RuntimeError('FRESH_QUEUE_FIXTURES_REQUIRED')
        self.legacy,self.base,self.names=copy.deepcopy(FIXTURES)
    def test_current_next_is_unaccepted_regular(self):
        index,name=g.old.select(self.base,self.names);self.assertNotIn(name,self.base['runtime_qualified_test_names'])
    def test_advance_works_for_next_and_following_without_code_change(self):
        index,_=g.old.select(self.base,self.names);next_plan=g.advance(self.legacy,self.base,self.names,index)
        following,_=g.old.select(next_plan,self.names);another=g.advance(self.legacy,next_plan,self.names,following)
        self.assertEqual(another['runtime_source_qualified_individual_cases'],self.base['runtime_source_qualified_individual_cases']+2)
    def test_advance_does_not_mutate_previous_queue(self):
        before=copy.deepcopy(self.base);g.advance(self.legacy,self.base,self.names,self.base['next_runtime_index'])
        self.assertEqual(before,self.base)
    def test_arbitrary_index_rejected(self):
        with self.assertRaises(ValueError):g.advance(self.legacy,self.base,self.names,249)
    def test_passed_index_rejected(self):
        with self.assertRaises(ValueError):g.advance(self.legacy,self.base,self.names,1)
    def test_pending_semantic_candidate_blocks_selection(self):
        self.base['runtime_successful_candidates_requiring_closing']=1
        with self.assertRaises(ValueError):g.advance(self.legacy,self.base,self.names,self.base['next_runtime_index'])
    def test_corpus_stays_excluded_not_skipped_as_pass(self):
        index=self.base['next_runtime_index'];self.names[index-1]=g.p.v.CORPUS_PREFIX+'mock'
        with self.assertRaises(ValueError):g.advance(self.legacy,self.base,self.names,index)
    def test_end_plan_does_not_promote_whole_or_Gate(self):
        result=g.advance(self.legacy,self.base,self.names,self.base['next_runtime_index'])
        self.assertFalse(result['whole1470_current_fresh_qualified']);self.assertFalse(result['full249_current_qualified'])
    def finish(self,error=None,reason=None,clean=True,validation=None):
        out=dict(state='FAILED_NOT_ACCEPTED',error_code=error);owner=SimpleNamespace(reason=reason)
        def cleanup(obj,doc):doc['resource_watcher_cleanup_confirmed']=clean
        with patch.object(g.p.b.s,'finish_watcher',cleanup):g.complete(out,owner,dict(state=g.PASS),validation or (lambda d:None))
        return out
    def test_success_published_only_after_cleanup_fields_present(self):
        def checked(doc):self.assertTrue(doc['resource_watcher_cleanup_confirmed']);self.assertIsNone(doc['resource_stop_reason'])
        self.assertEqual(self.finish(validation=checked)['state'],g.PASS)
    def test_post_validation_exception_cannot_leave_PASS(self):
        def invalid(doc):raise KeyError('resource_stop_reason')
        self.assertEqual(self.finish(validation=invalid)['state'],'FAILED_NOT_ACCEPTED')
    def test_existing_error_cannot_leave_PASS(self):self.assertEqual(self.finish(error='OWN_ERROR')['state'],'FAILED_NOT_ACCEPTED')
    def test_CPU_stop_cannot_leave_PASS(self):self.assertEqual(self.finish(reason='STOP_SUSTAINED_SYSTEM_CPU')['state'],'FAILED_NOT_ACCEPTED')
    def test_watcher_cleanup_failure_cannot_leave_PASS(self):self.assertEqual(self.finish(clean=False)['state'],'FAILED_NOT_ACCEPTED')
    def test_no_candidate_is_not_success(self):
        out=dict(state='FAILED_NOT_ACCEPTED');owner=SimpleNamespace(reason=None)
        with patch.object(g.p.b.s,'finish_watcher',lambda o,d:d.update(resource_watcher_cleanup_confirmed=True)):
            g.complete(out,owner,None,lambda d:None)
        self.assertEqual(out['state'],'FAILED_NOT_ACCEPTED')
    def test_bool_index_rejected(self):
        with self.assertRaises(ValueError):g.advance(self.legacy,self.base,self.names,True)
    def test_failed_overall_record_rejected_without_touching_source_or_body(self):
        with self.assertRaises(ValueError):g.record(dict(schema_version=g.SCHEMA,state='FAILED_NOT_ACCEPTED'),
            {},{}, {},{}, {}, self.names,self.legacy,self.base)
